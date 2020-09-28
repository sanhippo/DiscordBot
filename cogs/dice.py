import d20
import discord
from discord.ext import commands

from utils.functions import search_and_select, try_delete



class Dice(commands.Cog):
    """Dice and math related commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='2', hidden=True)
    async def quick_roll(self, ctx, *, mod: str = '0'):
        """Quickly rolls a d20."""
        rollStr = '1d20+' + mod
        await self.rollCmd(ctx, rollStr=rollStr)

    @commands.command(name='roll', aliases=['r'])
    async def rollCmd(self, ctx, *, rollStr: str = '1d20'):
        """Rolls dice in xdy format.
        __Examples__
        !r xdy Attack!
        !r xdy+z adv Attack with Advantage!
        !r xdy-z dis Hide with Heavy Armor!
        !r xdy+xdy*z
        !r XdYkhZ
        !r 4d6mi2[fire] Elemental Adept, Fire
        !r 2d6e6 Explode on 6
        !r 10d6ra6 Spell Bombardment
        !r 4d6ro<3 Great Weapon Master
        __Supported Operators__
        k (keep)
        p (drop)
        ro (reroll once)
        rr (reroll infinitely)
        mi/ma (min/max result)
        e (explode dice of value)
        ra (reroll and add)
        __Supported Selectors__
        X (literal X)
        lX (lowest X)
        hX (highest X)
        >X (greater than X)
        <X (less than X)"""

        if rollStr == '0/0':  # easter eggs
            return await ctx.send("What do you expect me to do, destroy the universe?")

        rollStr, adv = self._string_search_adv(rollStr)

        res = d20.roll(rollStr, advantage=adv, allow_comments=True, stringifier=VerboseMDStringifier())
        out = f"{ctx.author.mention}  :game_die:\n" \
              f"{str(res)}"
        if len(out) > 1999:
            out = f"{ctx.author.mention}  :game_die:\n" \
                  f"{str(res)[:100]}...\n" \
                  f"**Total:** {res.total}"

        await try_delete(ctx.message)
        await ctx.send(out, allowed_mentions=discord.AllowedMentions(users=[ctx.author]))


def setup(bot):
    bot.add_cog(Dice(bot))
    # Adds the Basic commands to the bot
    # Note: The "setup" function has to be there in every cog file

