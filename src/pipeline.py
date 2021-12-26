# Discord message pipeline
# Takes in message, parses it, and returns response.

import discord

embed_color = discord.Colour.from_rgb(215,195,134)

class Pipeline():
    def __init__(self, util=None, keys=None):
        self.util = util
        self.keys = keys
    
    def log(self, message):
        if self.util:
            self.util.log(self.__class__.__name__, message)
    
    def generate(self, message):
        return message

import wikipedia
from youtube_search import YoutubeSearch
from gpt3search import SearchService

class WikipediaPipeline(Pipeline):
    def __init__(self, util=None, keys=None):
        super().__init__(util, keys)
        self.log("Pipeline Initialized.")
    
    def generate(self, message):
        if not message:
            return "Please specify a search term."
        
        try:
            result_terms = wikipedia.search(message, results='5')
        except wikipedia.exceptions.DisambiguationError as e:
            result_terms = e.options
            result_terms.pop(0)
        
        if not result_terms:
            return "No results found."
        
        try:
            article = wikipedia.page(title=result_terms[0], auto_suggest=False)
            return article.url
        except wikipedia.exceptions.PageError:
            return "No results found."

class YoutubePipeline(Pipeline):
    def __init__(self, util=None, keys=None):
        super().__init__(util, keys)
        self.service = SearchService(api_key=keys["openai_token"])
        self.log("Pipeline Initialized.")

    def generate(self, message):
        if not message:
            return "Please specify a search term."
        
        results = YoutubeSearch(message, max_results=8)
        if not results:
            return 'Could not find YouTube video.'
        
        search_query = []
        for i in results.videos:
            search_query.append(i['title'])
        
        selection = self.service.classify_sequence(message, search_query)
        return 'https://www.youtube.com' + results.videos[selection]['url_suffix']

from pybooru import Danbooru

# returns an embed
# Message pipeline for Danbooru images.
class DanbooruPipeline(Pipeline):

    def __init__(self, util=None, keys=None):
        super().__init__(util, keys)
        self.nsfw_client = Danbooru('danbooru', username=keys["danbooru_username"], api_key=keys["danbooru_token"])
        self.sfw_client = Danbooru('safebooru', username=keys["danbooru_username"], api_key=keys["danbooru_token"])
        self.log("Pipeline Initialized.")

    def generate(self, message, nsfw, author):
        embed = discord.Embed()
        embed.set_footer(text=author.name + '#' + author.discriminator, icon_url=author.avatar_url)
        embed.colour = embed_color

        if not message:
            embed.title = 'Error'
            embed.description = 'Please input a search term!'
            return embed
        
        if nsfw:
            output = self.nsfw_client.post_list(tags=message, limit=1, random=True)
        else:
            output = self.sfw_client.post_list(tags=message, limit=1, random=True)
        if not output:
            embed.title = 'Error'
            embed.description = 'Post not found.'
            return embed
        
        embed.title = message

        try:
            embed.set_image(url=output['file_url'])
            embed.url = output['file_url']
            return embed
        except:
            try:
                embed.set_image(url=output[0]['file_url'])
                embed.url = output[0]['file_url']
                return embed
            except:
                embed.title = 'Error'
                embed.description = 'Post not found.'
                return embed


from gptj import GPTJGeneratorService
from gpt3 import GPT3GeneratorService

# Q&A Pipeline
class QnAPipeline(Pipeline):
    def __init__(self, util=None, keys=None):
        super().__init__(util, keys)
        try:
            self.model = GPTJGeneratorService(ip=keys["sukima_ip"], username=keys["sukima_username"], password=keys["sukima_password"])
        except:
            self.log("Failed to initialize. Auth timeout.")
        self.log("Pipeline Initialized.")
        self.prompt = "{author}: How does a telescope work?\nRan Yakumo: Telescopes use lenses or mirrors to focus light and make objects appear closer.\n{author}: {question}\nRan Yakumo:"
    
    def generate(self, message, author):
        embed = discord.Embed()
        embed.set_footer(text=author.name + '#' + author.discriminator, icon_url=author.avatar_url)
        embed.colour = embed_color

        prompt_formatted = self.prompt.format(question=message, author=author.name)
        prompt_formatted = prompt_formatted[0:400] # 400 character limit
        response = self.model.sample_sequence_raw(prompt_formatted)
        embed.description = response
        
        return embed

# Dictionary Pipeline
class DictionaryPipeline(Pipeline):
    def __init__(self, util=None, keys=None):
        super().__init__(util, keys)
        try:
            self.model = GPTJGeneratorService(ip=keys["sukima_ip"], username=keys["sukima_username"], password=keys["sukima_password"])
        except:
            self.log("Failed to initialize. Auth timeout.")
        self.log("Pipeline Initialized.")
        self.prompt = "world - the earth, together with all of its countries, peoples, and natural features.\nbrain - an organ of soft nervous tissue having a grayish-white surface and a number of minute blood vessels, functioning as the center of the nervous system.\nlinker (programming) - a program that links the source code of a software program into a single executable file.\nintracranial hemorrhaging - the process of bleeding within the brain.\npresident - a person who presides over an organization, usually with the title of chairman.\nsenator - a person who is elected to represent a state in the U.S. Senate.\nvirtual machine - a computer program that emulates the behavior of a real machine.\nhole - a small opening or cavity.\n{term} -"

    def generate(self, message, author):
        embed = discord.Embed()
        embed.set_footer(text=author.name + '#' + author.discriminator, icon_url=author.avatar_url)
        embed.colour = embed_color

        prompt_formatted = self.prompt.format(term=message)
        response = self.model.sample_sequence_raw(prompt_formatted)
        embed.description = response

        return embed

# Message pipeline for translation tasks.
class TranslationPipeline(Pipeline):

    def __init__(self, util=None, keys=None):
        super().__init__(util, keys)
        self.model = GPT3GeneratorService(generate_num=32, temperature=0.33, model_name='davinci', api_key=keys["openai_token"])
        self.prompt = "This is a translation from {from_lang} to {to_lang}.\n{from_lang}: {message}\n{to_lang}:"
        self.tl_configurations = {
            'ja': 'Japanese',
            'en': 'English',
            'es': 'Spanish',
            'br': 'Brazilian',
            'pt': 'Portuguese',
            'fr': 'French',
            'it': 'Italian',
            'de': 'German',
            'ru': 'Russian',
            'ko': 'Korean',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'nl': 'Dutch',
            'fi': 'Finnish',
            'fr': 'French',
            'hi': 'Hindi',
            'id': 'Indonesian'
        }

        self.log("Pipeline initialized.")
    
    def generate(self, message, from_lang, to_lang):
        # log from language and to language

        if from_lang not in self.tl_configurations:
            return "Invalid language code."
        if to_lang not in self.tl_configurations:
            return "Invalid language code."
        
        prompt_formatted = self.prompt.format(from_lang=self.tl_configurations[from_lang], to_lang=self.tl_configurations[to_lang], message=message)
        prompt_formatted = prompt_formatted[0:400] # 400 character limit
        response = self.model.sample_sequence_raw(prompt_formatted)

        if response == '':
            response = 'Unable to translate.'

        return response
