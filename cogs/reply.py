from discord.ext.commands import Cog, command
from discord.utils import get
from discord.errors import InvalidArgument
from discord import Webhook, AsyncWebhookAdapter, Embed, File
from urllib.request import Request, urlopen
import aiohttp
import os


class Reply(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_to_user = {}
        self.emoji = b'\xe2\x9c\x89\xef\xb8\x8f'
        self.IMG_EXT = [".jpg", ".png", ".jpeg", ".gif", ".gifv"]
        self.VIDEO_EXT = ['.mp4', '.avi', '.flv', '.mov', 'wmv']

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        When a reaction is added to any message the user and that message are linked
        within a message_to_user dictionary
        Users can only reply to one message at a time therefore if a user
        reacts to a new message when their id is already within message_to_user dictionary,
        the old message id gets overwritten by the new one

        Multiple users can react to the same message
        """
        with open("emoji", "r", encoding="utf-8") as f:
            self.emoji = f.read().encode('utf-8')
        #   If user has a message queued up to be replied to it will be overwritten
        if payload.user_id in self.message_to_user.keys():
            del self.message_to_user[payload.user_id]
        if payload.emoji.name == self.emoji.decode():
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            user = self.bot.get_user(payload.user_id)
            self.message_to_user[user.id] = message.id

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        If a user removes their reaction from a message his id
        is removed from the message_to_user dict which removes
        him from the reply queue

        This also gets called when the bot itself removes reactions
        but is ignored
        """
        #   payload.user_id actually returns the user whose emoji got removed
        #   instead of returning the id of the user who removed it
        with open("emoji", "r", encoding="utf-8") as f:
            self.emoji = f.read().encode('utf-8')
        if payload.emoji.name == self.emoji.decode():
            if self.message_to_user.get(payload.user_id):
                del self.message_to_user[payload.user_id]

    @Cog.listener()
    async def on_message(self, msg):
        """
        When a message is sent check if that message is actually a reply
        to another message and if so delete it and turn it into a webhooked reply
        """
        if msg.author.id in list(self.message_to_user.keys()):
            if msg.attachments:
                req = Request(url=msg.attachments[0].url, headers={'User-Agent': 'Mozilla/5.0'})
                webpage = urlopen(req).read()
                with open(msg.attachments[0].filename, 'wb') as f:
                    f.write(webpage)

        if msg.author.id in list(self.message_to_user.keys()):
            message = await msg.channel.fetch_message(self.message_to_user[msg.author.id])
            del self.message_to_user[msg.author.id]
            webhook = await msg.channel.create_webhook(name="Placeholder")
            await self.send_message(msg.author, await self.create_embed(message.author, message), msg, webhook)
            await webhook.delete()
            emoji = get(msg.channel.guild.emojis, name=self.emoji.decode())
            try:
                await message.remove_reaction(emoji, msg.author)
            except InvalidArgument:
                await message.remove_reaction(self.emoji.decode(), msg.author)
            await msg.delete()

    async def create_embed(self, author, author_message):
        """
        Create the embed with the contents of the message that is being
        replied to
        :param author: Author (User object) of the message
        :param author_message: The contents of the message
        :return: Embed object with the message contents and user info along with
        hyperlink to the message being replied to
        """
        embed = Embed(color=author.color)

        if author_message.clean_content:
            embed.add_field(name=author.display_name, value=author_message.clean_content)
        else:
            embed.add_field(name=author.display_name, value="\u200b")

        if author_message.attachments:
            for att in author_message.attachments:
                for ext in self.IMG_EXT:
                    if ext in att.filename:
                        break
                else:
                    for ext in self.VIDEO_EXT:
                        if ext in att.filename:
                            embed.add_field(name="\u200b", value=f"🎞️ {att.filename}", inline=False)
                            break
                    else:
                        embed.add_field(name="\u200b", value=f"📁 {att.filename}", inline=False)
                        break
                    break
                embed.set_image(url=f"{att.url}")

        if author_message.embeds and not author_message.attachments:
            for embed in author_message.embeds:
                embed.clear_fields()
                embed.set_image(url="")
                embed.add_field(name=author.display_name, value=author_message.clean_content)

        embed.set_thumbnail(url=author.avatar_url_as(size=128, format='png'))
        embed.add_field(name="\u200b", value=f"[⏫⏫⏫⏫]({author_message.jump_url})", inline=False)

        return embed

    async def send_message(self, original_user, embed, message, webhook):
        """
        Sends a message impersonating the user that called the reply
        functionality
        :param original_user: User who send the reply message
        :param embed: Embed object that contains original_user info and message content
        :param message: Message of the reply that original_user sent
        :param webhook: Webhook that will get customized to impersonate original_user
        """
        avatar_url = original_user.avatar_url_as(size=128, format='png')
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(webhook.url, adapter=AsyncWebhookAdapter(session))

            if message.attachments:
                for att in message.attachments:
                    for ext in self.IMG_EXT:
                        if ext in att.filename:
                            with open(att.filename, 'rb') as f:
                                await webhook.send(embed=embed,
                                                   content=message.content,
                                                   username=original_user.display_name,
                                                   avatar_url=avatar_url,
                                                   file=File(f)
                                                   )

                            os.remove(att.filename)
                            return
                    else:
                        for ext in self.VIDEO_EXT:
                            if ext in att.filename:
                                with open(att.filename, 'rb') as f:
                                    await webhook.send(embed=embed,
                                                       content=message.content,
                                                       username=original_user.display_name,
                                                       avatar_url=avatar_url,
                                                       file=File(f)
                                                       )
                                os.remove(att.filename)
                                return
                        else:
                            with open(att.filename, 'rb') as f:
                                await webhook.send(embed=embed,
                                                   content=message.content,
                                                   username=original_user.display_name,
                                                   avatar_url=avatar_url,
                                                   file=File(f)
                                                   )
                            os.remove(att.filename)
                            return

            await webhook.send(embed=embed,
                               content=message.content,
                               username=original_user.display_name,
                               avatar_url=avatar_url
                               )

    @command(aliases=['change', 'change_emoji', 'replace_emoji', 'emoji_change', 'emoji_replace'])
    async def replace(self, ctx, emoji):
        """
        Used to replace the emoji you want to use as a reply button
        :param ctx: Context of the command to get from which channel it was called
        :param emoji: The string of the emoji (if it's a custom one strip it of the id part
        :return: Writes the emoji in the emoji file
        """
        await ctx.message.channel.send(f"Reply emoji changed to {emoji}")
        if '<' in emoji:
            emoji = emoji.split(':')[1]
        with open("emoji", "wb") as f:
            f.write(emoji.encode('utf-8'))
