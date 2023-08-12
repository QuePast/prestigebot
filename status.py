import discord
from discord.ext import commands
import asyncio
import aiohttp

discord_bot = "xxxxxxxx"

# Subscribed users and their thresholds
subscribed_users = {}

# Load subscribed user data from file
def load_subscribed_users():
    try:
        with open('info.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                parts = line.strip().split(',')
                user_id = int(parts[0])
                email = parts[1]
                password = parts[2]
                threshold = int(parts[3])
                subscribed_users[user_id] = {
                    'email': email,
                    'password': password,
                    'threshold': threshold
                }
    except FileNotFoundError:
        pass

# Save subscribed user data to file
def save_subscribed_users():
    with open('info.txt', 'w') as file:
        for user_id, subscription in subscribed_users.items():
            line = f"{user_id},{subscription['email']},{subscription['password']},{subscription['threshold']}\n"
            file.write(line)

async def fetch_server_status(subscribed_user):
    login_url = 'https://prestigebot.com/api/auth/login'
    api_url = 'https://prestigebot.com/api/page/home'
    email = subscribed_user['email']
    password = subscribed_user['password']

    async with aiohttp.ClientSession() as session:
        login_data = {
            'email': email,
            'password': password
        }

        async with session.post(login_url, json=login_data) as login_response:
            if login_response.status == 200:
                #print("Login successful")

                # Extract the authorization token from the login response
                authorization_token = (await login_response.json()).get('token', '')

                # Make a GET request to the API endpoint with the authorization header
                headers = {
                    'Authorization': authorization_token
                }
                async with session.get(api_url, headers=headers) as api_response:
                    if api_response.status == 200:
                        try:
                            data = await api_response.json()

                            # Extract the 'running_machines' value and return it as an integer
                            if 'running_machines' in data[0]:
                                running_machines = data[0]['running_machines']
                                # print(f"Number of running machines: {running_machines}")
                                return int(running_machines)
                            else:
                                print("Running machines information not found in the data")
                                return 0  # Return 0 as a default value
                        except Exception as e:
                            print(f"Error parsing API response: {e}")
                            return 0  # Return 0 as a default value
                    else:
                        print(f"API request failed with status code: {api_response.status}")
                        return 0  # Return 0 as a default value
            else:
                print(f"Login failed with status code: {login_response.status}")
                return 0  # Return 0 as a default value

#Bot stuff
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.command()
async def subscribe(ctx, email: str, password: str, threshold: int):
    # Store the user's subscription details
    subscribed_users[ctx.author.id] = {
        'email': email,
        'password': password,
        'threshold': threshold
    }
    
    # Save the subscription data to the file
    save_subscribed_users()
    
    # Fetch server status using the user's data
    subscribed_user = subscribed_users[ctx.author.id]
    current_status = await fetch_server_status(subscribed_user)

    if current_status < threshold:
        await ctx.author.send(f"**Active Bots:** {current_status}/{threshold} {ctx.author.mention}")


@bot.event
async def on_ready():
    # Load subscribed users from file
    load_subscribed_users()

    while True:
        await asyncio.sleep(600)  # update every 10 minutes

        for user_id, subscription in subscribed_users.items():
            current_status = await fetch_server_status(subscription)
            if current_status < subscription['threshold']:
                user = await bot.fetch_user(user_id)
                await user.send(f"**Active Bots:** {current_status}/{subscription['threshold']} {user.mention}")

bot.run(discord_bot)