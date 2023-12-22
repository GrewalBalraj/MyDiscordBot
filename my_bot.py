import os
import discord 
import requests
import random
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from AnilistPython import Anilist
from requests_cache import CachedSession

# Loads the environmental variables 
load_dotenv()

# Gets the API Key for the Discord bot 
token = os.getenv("API_KEY")

# Gets Weather API Key
weather_key = os.getenv("WEATHER_KEY")


class MyBot(commands.Bot):

    # CLASS VARIABLES START

    # Creates a cached session that will hold the names of pokemon recently accessed
    # Will be used to limit the number of API calls to PokeAPI (Since PokeAPI calls will be the same)
    session = CachedSession('poke_cache', expire_after=360)

    # CLASS VARIABLES END
    
    def __init__(self, command_prefix):

        commands.Bot.__init__(self, command_prefix=command_prefix, intents=discord.Intents.all())

        # Adds all the bot commands
        self.add_commands()


    async def on_ready(self):
        print(f"{self.user} logged in")


    async def on_message(self, msg):
         
        """on_message event function runs each time a message
        is sent in the discord, and will moderate any messages
        that are sent"""

        # List that will be used to prevent unwanted links from being displayed on server
        unwanted_links = ["https://", "http://"]

        # Iterates through each word in the unwanted_links list
        for word in unwanted_links:

            # If word (link) is in message, deletes the message and returns
            if word in str(msg.content.lower()):
                await msg.delete()
                return
    
        # Allows bot to run any commands after message has been checked
        await self.process_commands(msg)


    # Add_commands to add commands onto the bot
    def add_commands(self):

        # TRIVIA COMMAND
        @self.command()
        async def trivia(ctx):

            """ trivia function command makes bot provide the user with 
            a multiple choice question and print a discord message to 
            the user depending on whether they got the question correct """
    
            # Creates a variable for the quiz api 
            quiz_url = "https://opentdb.com/api.php?amount=1&difficulty=medium&type=multiple"

            # Creates and initializes response to the value returned by the get request for quiz_url
            response = requests.get(quiz_url)

            # Creates a variable to hold the discord channel the trivia command was called in
            channel = ctx.message.channel

            # response_data is created and intialized to the json-encoded content of response
            response_data = response.json()

            # Creates a "discord bot is typing" prompt whilst the following processes are being completed
            async with channel.typing():

                # Extracts quiz question from response_data and replaces any formatting issues
                question = response_data["results"][0]["question"]
                question = question.replace("&quot;", "")
                question = question.replace("&#039;", "'")
        
                # Extracts correct answer from response_data
                answer = response_data["results"][0]["correct_answer"]

                # Extracts list of all the incorrect answers from response_data
                all_answers = response_data["results"][0]["incorrect_answers"]

                # Appends correct answer onto list of all wrong answers, then randomizes order of list
                all_answers.append(answer)
                random.shuffle(all_answers)

                # Creates a discord embed which is titled with the quiz question
                embed = discord.Embed(title=question)

                # Adds potenial answer fields to the embed
                embed.add_field(name=f"1.)",  value={all_answers[0]}, inline=True)
                embed.add_field(name=f"2.)", value={all_answers[1]}, inline=False)
                embed.add_field(name=f"3.)", value={all_answers[2]}, inline=False)
                embed.add_field(name=f"4.)", value={all_answers[3]}, inline=True)
        
                # Sets embed footer to remind user of correct format of their answer
                embed.set_footer(text="Choose the number corresponding to your answer")
                await channel.send(embed=embed)

                def check(message):

                    """ Check runs a simple check on a message to see if the
                    author of the message is the same as the command author,
                    then ensures that the message was an digit"""
            
                    return message.author == ctx.author and message.content.isdigit()
        
                try:

                    # Creates a guess variable that holds the user's guess to the question
                    # Makes sure user's message was a digit and gives user 15s to answer
                    guess = await self.wait_for('message', check=check, timeout=15.0)
        
                # Except block that catches a TimeoutError
                except asyncio.TimeoutError:

                    # Returns a message telling user they took too long to answer
                    return await channel.send("Sorry, you took too long")
        
                # Compares the user's answer to the correct answer 
                if all_answers[int(guess.content)-1] == answer:

                    # Sends message that user was correct
                    await channel.send("You are correct!!!")
                else:

                    # Sends message that user was wrong
                    await channel.send("Oops! That is not the right answer.")


            
        # WEATHER COMMAND
        @self.command()
        async def weather(ctx, *, city_name: str):

            """ Weather command allows the user to enter a city name
            and the discord bot will return the weather of that area
        
            :param city_name: The name of a city user wants weather from"""
    
            # Base url for the weather API
            weather_url = "http://api.openweathermap.org/data/2.5/weather?"
            city = city_name

            # Creates the full url for the weather API using base url and weather API key 
            full_url = weather_url + "appid=" + weather_key + "&q=" + city + "&units=metric" 

            # Creates and initializes response to the  value returned by the get request for full_url
            response = requests.get(full_url)

            # Creates response_data and initializes to the json-encoded content of response_data
            response_data = response.json()

            # Creates channel to hold the channel for the 
            channel = ctx.message.channel

            # Checks if response_data is holding valid weather data
            if response_data["cod"] != "404":

                # Creates a "discord bot is typing" prompt whilst the following processes are being completed
                async with channel.typing():

                    # Creates weather_data to hold the weather information in response_data
                    weather_data = response_data["main"]

                    # Creates variables to hold the temperature, humidity, and weather description
                    current_temp = weather_data["temp"]
                    humidity = weather_data["humidity"]
                    weather_desc = response_data["weather"][0]["description"]

                    # creates a discord embed that is titled with "weather in" followed by a city
                    embed = discord.Embed(title=f"Weather in {city}", timestamp=ctx.message.created_at)

                    # Adds a weather description, temperature, and humidity field to embed
                    embed.add_field(name="Description", value=f"{weather_desc}", inline=False)
                    embed.add_field(name="Temperature(C)", value=f"{current_temp}°C", inline=False)
                    embed.add_field(name="Humidity(%)", value=f"{humidity}%", inline=False)

                    # Sets the thumbnail for embed to a weather image
                    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/4851/4851776.png")

                    # Sends the weather embed message to the channel
                    await channel.send(embed=embed)

            else:

                # Bot sends an error message to the user
                await channel.send("City not found")



        # POKEDEX_ENTRY COMMAND
        @self.command()
        async def pokedex_entry(ctx, number: int):

            """Pokedex_entry command allows the user to enter
            an integer and recieve the pokemon who corresponds 
            to that number """

            # Gets the channel command was sent in
            channel = ctx.message.channel

            async with channel.typing():

                # Checks if number given was less than 0
                if number <= 0:

                    # Bot sends message to let user know there is no pokemon with that number
                    await channel.send(f"There is no Pokemon with that number")
                    return
            
                # Creates url for the PokeAPI
                poke_url = "https://pokeapi.co/api/v2/pokemon/"

                # Creates params for the API call, with 'limit': 1
                params = {'limit': 1}

                # Sets params['offset'] to the number associated with the requested pokemon
                params['offset'] = int(number) - 1

                # response is set to the content returned the get request to PokeAPI using the specified params
                response = self.session.get(poke_url, params=params)

                # reponse_data is created and initialized to the json-encoded content of response
                response_data = response.json()

                try:

                    # Bot sends a message with the name of the pokemon found
                    await channel.send(response_data['results'][0]['name'])
            
                except IndexError:

                    # Bot sends message to let user know there is no pokemon with that number
                    await channel.send(f"There is no Pokemon with that number")



        # ANIME_DESC COMMAND
        @self.command()
        async def anime_desc(ctx, *, name):
    
            """anime_desc command allows user to get information
            on a variety of different manga and anime, as well
            as get information on specific characters
        
            :param name: name of anime, manga, or character"""
    
            # Initialize an instance to the Anilist API.
            anilist = Anilist()

            # Gets the channel command was made in
            channel = ctx.message.channel

            # list for all the possible options user can find info on 
            options = ["anime", "manga", "character"]

            async with channel.typing():

                # Sends a message asking user what they are looking for information about
                await channel.send("What are you looking for info on? [ anime, manga, character ]")

            def check (message):

                """Check function that ensures the author of the command
                made another message that contained one of the option types"""
        
                return message.author == ctx.author and message.content.lower() in options
    
            try:

                # Creates a variable that holds user's option selection
                # Gives user 15s to reply
                options_type = await self.wait_for('message', check=check, timeout=15.0)

                async with channel.typing():

                    # Bot sends the anime description if options_type is "anime"
                    if options_type.content.lower() == "anime":
                            
                        try:

                            await channel.send(anilist.get_anime(name)['desc'].replace("<br>", ""))
                        
                        # In case description is too long
                        except discord.errors.HTTPException:

                            # Gets the anime description
                            desc = anilist.get_anime(name)['desc'].replace("<br>", "")

                            # Splits discription into chunks of 2000 characters
                            chunks = [desc[i:i+2000] for i in range(0, len(desc), 2000)]

                            # Creates a counter (used to number each part of the description)
                            counter = 0

                            # For each chunk of characters, creates an embed with that chunk of the description
                            for chunk in chunks:
                                counter += 1 
                                embed = discord.Embed(title=f"{name} Description, Part {counter}", description=chunk) 
                                await channel.send(embed=embed)
                        
                    # Bot sends the manga description if options_type is "manga"
                    elif options_type.content.lower() == "manga":

                        try:

                            await channel.send(anilist.get_manga(name)['desc'].replace("<br>", ""))
                        
                        # In case description is too long
                        except discord.errors.HTTPException:

                            # Gets the manga description
                            desc = anilist.get_manga(name)['desc'].replace("<br>", "")

                            # Splits discription into chunks of 2000 characters
                            chunks = [desc[i:i+2000] for i in range(0, len(desc), 2000)]

                            # Creates a counter (used to number each part of the description)
                            counter = 0

                            # For each chunk of characters, creates an embed with that chunk of the description
                            for chunk in chunks: 
                                counter += 1
                                embed = discord.Embed(title=f"{name} Description, Part {counter}", description=chunk) 
                                await channel.send(embed=embed)


                    # Bot sends the character description if options_type is "character"
                    elif options_type.content.lower() == "character":

                        try:

                            await channel.send(anilist.get_character(name)['desc'].replace("<br>", ""))
                        
                        # In case description is too long
                        except discord.errors.HTTPException:

                            # Gets the character description
                            desc = anilist.get_character(name)['desc'].replace("<br>", "")

                            # Splits discription into chunks of 2000 characters
                            chunks = [desc[i:i+2000] for i in range(0, len(desc), 2000)]

                            # Creates a counter (used to number each part of the description)
                            counter = 0

                            # For each chunk of characters, creates an embed with that chunk of the description
                            for chunk in chunks: 
                                counter += 1
                                embed = discord.Embed(title=f"{name} Description, Part {counter}", description=chunk) 
                                await channel.send(embed=embed)

            # Except block that catches an IndexError
            except IndexError:
                
                async with channel.typing():

                    # Sends an error message if the bot could not find the character, manga, or anime
                    await channel.send(f"Could not find what you are looking for. Sorry!")

            # Except block that catches a TimeoutError
            except asyncio.TimeoutError:
                
                async with channel.typing():

                    # Sends an error message that the user took too long
                    await channel.send(f"Sorry, you took too long.")



if __name__ == "__main__":
    bot = MyBot(command_prefix="/")
    bot.run(token)