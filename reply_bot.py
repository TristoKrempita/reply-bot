from discord.ext.commands import Bot, HelpCommand
from discord import Embed
from cogs.reply import Reply

client = Bot(command_prefix="!")

client.remove_command('help')
client.add_cog(Reply(client))

@client.command()
async def help(ctx):
    embed = Embed(color=0x990000)
    embed.add_field(name="The Reply Bot", value="\u200b")
    embed.set_thumbnail(url="https://cdn4.iconfinder.com/data/icons/email-2-2/32/Reply-all-Email-512.png")
    embed.add_field(name="Description:", value="A bot that adds reply functionality to Discord")
    embed.add_field(name="Usage:", value="To reply to a message simply react to a message with ✉ and write your response")
    await ctx.message.channel.send(embed=embed)

client.run('BOT_SECRET')
