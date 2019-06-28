from discord.ext.commands import Cog, command
from discord import Embed, File
import aiohttp
from discord import Webhook, AsyncWebhookAdapter
from urllib.request import Request, urlopen
import os

class Reply(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_to_user = {}
        self.emoji = '✉'
        self.IMG_EXT = [".jpg", ".png", ".jpeg", ".gif", ".gifv"]
        self.VIDEO_EXT = ['.mp4', '.avi', '.flv', '.mov', 'wmv']

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        with open("emoji", "r", encoding="utf-8") as f:
            self.emoji = f.read()
        #   If user has a message queued up to be replied to it will be overwritten
        if payload.user_id in self.message_to_user.values():
            del self.message_to_user[dict(zip(self.message_to_user.values(), self.message_to_user.keys()))[payload.user_id]]
        if payload.emoji.name == self.emoji:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            user = self.bot.get_user(payload.user_id)
            self.message_to_user[message.id] = user.id

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        with open("emoji", "r", encoding="utf-8") as f:
            self.emoji = f.read()
        if payload.emoji.name == self.emoji:
            print("User removed from replying")
            channel = self.bot.get_channel(payload.channel_id)
            msg = await channel.fetch_message(payload.message_id)
            del self.message_to_user[msg.id]

    @Cog.listener()
    async def on_message(self, msg):
        if msg.author.id in list(self.message_to_user.values()):
            if msg.attachments:
                req = Request(url=msg.attachments[0].url, headers={'User-Agent': 'Mozilla/5.0'})
                webpage = urlopen(req).read()
                with open(msg.attachments[0].filename, 'wb') as f:
                    f.write(webpage)

            message = await msg.channel.fetch_message(dict(zip(self.message_to_user.values(), self.message_to_user.keys()))[msg.author.id])
            del self.message_to_user[message.id]
            webhook = await msg.channel.create_webhook(name="Placeholder")
            await self.send_message(msg.author, await self.create_embed(message.author, message), msg, webhook)
            await webhook.delete()
            await message.clear_reactions()
            await msg.delete()

    async def create_embed(self, author, author_message):
        embed = Embed(color=author.color)

        if author_message.clean_content:
            embed.add_field(name=author.display_name, value=author_message.clean_content)
        else:
            embed.add_field(name=author.display_name, value="\u200b")

        # if author_message.attachments:
        #     print(author_message.attachments[0])

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

        embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{author.id}/{author.avatar}.png?size=128")
        embed.add_field(name="\u200b", value=f"[⏫⏫⏫⏫]({author_message.jump_url})", inline=False)

        return embed

    async def send_message(self, original_user, embed, message, webhook):
        avatar_url = f"https://cdn.discordapp.com/avatars/{original_user.id}/{original_user.avatar}.png?size=128"
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
        await ctx.message.channel.send(f"Reply emoji changed to {emoji}")
        if '<' in emoji:
            emoji = emoji.split(':')[1]
        with open("emoji", "w", encoding="utf-8") as f:
            f.write(emoji)
