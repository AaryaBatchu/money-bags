import discord
from discord.ext import commands


# intents = discord.Intents.all()
help_command = commands.DefaultHelpCommand(no_category="**Commands**")
bot = commands.Bot(command_prefix="$$", intents=discord.Intents.all())


wallets = {}
everyones_names = {}
auctions = []
bounties = []
started = False
initial_val = 0


@bot.event
async def on_ready():
    # print("Online. Logged in as {0.user}".format(bot))

    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")

    # Setting `Playing` status
    await bot.change_presence(activity=discord.Game(name="Giving people $$!"))

    # Setting `Streaming` status
    # await bot.change_presence(activity=discord.Streaming(name="Giving people $$!", url='www.google.com'))

    # Setting `Listening` status
    # await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Giving people $$"))

    # Setting `Watching` status
    # await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Giving people $$!"))


@bot.event
async def on_member_join(member):
    print("%s joined" % member.mention)
    if started:
        wallets[member.id] = initial_val
        if member.nick is None:
            everyones_names[member.id] = member.name
        else:
            everyones_names[member.id] = member.nick

        try:
            await member.edit(nick=(everyones_names[member.id] + " {$%d}" % wallets[member.id]))
            print(everyones_names[member.id] + " {$%d}" % wallets[member.id])
        except discord.errors.Forbidden:
            pass

        try:
            await member.guild.system_channel.send("Welcome, %s. Here's $%d! \nEnjoy!" % (member.mention, initial_val))
        except AttributeError:
            for channel in member.guild.channels:
                if type(channel) == discord.TextChannel:
                    await channel.send("Welcome, %s. Here's $%d! \nEnjoy!" % (member.mention, initial_val))
                    return


class BasicCommands(commands.Cog):
    """The basic commands for starting $$ and sharing the wealth."""

    @commands.command()
    async def give(self, ctx, val):
        """Gives some of your money to your friend(s)"""
        if not started:
            return
        if val.startswith("$"):
            val = val[1:]
            gift_val = int(val)
        elif val == "all" or val == "-a":
            gift_val = int(wallets[ctx.message.author.id])
        else:
            gift_val = int(val)

        if gift_val < 0:
            await ctx.reply("You can't give negative money (that would be stealing)")

        giver = ctx.message.author

        recipients = []
        recipient_str = []

        for recipient in ctx.message.mentions:
            recipients.append(recipient.id)
            recipient_str.append(str(recipient.mention))

        if gift_val * len(recipients) <= wallets[giver.id]:
            giver_wallet = wallets[giver.id] - (gift_val * len(recipients))

            recipients_wallet = {}
            for recipient in recipients:
                recipients_wallet[recipient] = (wallets[recipient] + gift_val)

            if len(recipient_str) == 1:
                each = ". "
            else:
                each = " each. "

            message = await ctx.channel.send("%s gave %s $%d%s"
                                             "\n\nThis will result in %s having $%d. "
                                             "\n\nReact to this message with :thumbsup: to confirm or :x: to cancel."
                                             % (giver.mention, ', '.join(recipient_str), gift_val, each, giver.mention, giver_wallet))

            await message.add_reaction("👍")
            await message.add_reaction("❌")

            global confirmed
            confirmed = False

            def check(confirmation_emoji, user):

                print("checking")
                global confirmed
                confirmed = str(confirmation_emoji.emoji) == "👍"

                return confirmation_emoji.message == message and user == giver and \
                       (str(confirmation_emoji.emoji) == "👍" or str(confirmation_emoji.emoji) == "❌")

            await bot.wait_for('reaction_add', check=check)

            if confirmed:
                wallets[giver.id] = giver_wallet

                for recipient in recipients:
                    wallets[recipient] = recipients_wallet[recipient]

                for member in ctx.guild.members:
                    try:
                        await member.edit(nick=(everyones_names[member.id] + " {$%d}" % wallets[member.id]))
                        print(everyones_names[member.id] + " {$%d}" % wallets[member.id])
                    except discord.errors.HTTPException:
                        print("Nick too long or is owner")
                        pass

                await ctx.channel.send("Confirmed.")
            else:
                await ctx.channel.send("Canceled.")

        else:
            await ctx.reply("Sorry, you don't have enough $$ for that.")

    @commands.command()
    async def wallet(self, ctx):
        """Checks the wallet value for a user"""
        if started:
            if "@everyone" in ctx.message.content or "everyone" in ctx.message.content:
                message = ""
                for member in ctx.guild.members:
                    message += "%s has $%d.\n" % (member.mention, wallets[member.id])
                await ctx.channel.send(message)
            elif len(ctx.message.mentions) == 0:
                await ctx.channel.send("You have $%d in your wallet." % wallets[ctx.message.author.id])
            else:
                message = ""
                for user in ctx.message.mentions:
                    message += "%s has $%d.\n" % (user.mention, wallets[user.id])

                await ctx.channel.send(message)
        else:
            await ctx.channel.send("$$ not started yet.")

    @commands.command()
    async def richest(self, ctx):
        """Tells you who's the richest"""
        if not started:
            await ctx.reply("$$ not started yet. Contact and admin to do $$start")
            return

        richest_val = -999
        richest_mention = ""
        tied = []
        for user in wallets.keys():
            if wallets[user] > richest_val:
                richest_val = wallets[user]
                richest_mention = bot.get_user(user).mention
                tied = []
            elif wallets[user] == richest_val and richest_val is not -999:
                if len(tied) == 0:
                    tied.append(richest_mention)
                tied.append(bot.get_user(user).mention)

        if len(tied) > 0:
            final_message = "Congrats to "
            for user in tied:
                final_message += "%s, " % user
            final_message += "you are tied for richest with $%d each." % richest_val
            await ctx.channel.send(final_message)
        elif bot.get_user(ctx.message.author.id).mention == richest_mention:
            await ctx.channel.send("**YOU**, %s, are the richest in all the land. "
                                   "\n\nYou have $%d in your wallet."
                                   % (richest_mention, richest_val))
        else:
            await ctx.channel.send("%s is the richest in all the land. They have $%d in their wallet."
                                   % (richest_mention, richest_val))

    @commands.command()
    async def syntax(self, ctx):
        """Lists the syntax for each command"""
        await ctx.channel.send("```$$start [initial_value] –– gives everyone $initial_value and "
                               "starts the $$ (can only be run by server admin)"
                               "\n\n$$give [gift_amount] @user (@user2 @user etc.) –– gives your friends"
                               "money from your own wallet (will give the gift_amount to each recipient "
                               "(And make sure the $$ has been started by an admin already)"
                               "\n\n$$wallet [@user] –– checks the wallet balance of user (if left blank"
                               "will check the message author's wallet balance) (if @ everyone it will"
                               "check everyone's balance```")

    @give.error
    async def give_error(self, ctx, error):
        err_message = "Invalid syntax. \nSyntax: ```$$give [gift amount] @user (@user2 @user etc.)``` " \
                      "\n\n(And make sure it has been started by an admin already)"

        # if isinstance(error, commands.BadArgument):
        #     err_message = "Invalid syntax. \nSyntax: $$start xx"
        # if isinstance(error, commands.BadArgument):
        #     err_message = "Invalid syntax. \nSyntax: $$start xx"
        # if isinstance(error, commands.BadArgument):
        #     err_message = "Invalid syntax. \nSyntax: $$start xx"
        # if isinstance(error, commands.BadArgument):
        #     err_message = "Invalid syntax. \nSyntax: $$start xx"

        await ctx.reply(err_message)

    @wallet.error
    async def wallet_error(self, ctx, error):
        err_message = "Invalid syntax. \nSyntax: ```$$wallet (@user @user2 @user etc.)``` " \
                      "\nIf no users listed, will return wallet of message author" \
                      "\n\n(And make sure it has been started by an admin already)"

        # if isinstance(error, commands.BadArgument):
        #     err_message = "Invalid syntax. \nSyntax: $$start xx"
        # if isinstance(error, commands.BadArgument):
        #     err_message = "Invalid syntax. \nSyntax: $$start xx"
        # if isinstance(error, commands.BadArgument):
        #     err_message = "Invalid syntax. \nSyntax: $$start xx"
        # if isinstance(error, commands.BadArgument):
        #     err_message = "Invalid syntax. \nSyntax: $$start xx"

        await ctx.reply(err_message)

    @richest.error
    async def richest_error(self, ctx, error):
        err_message = "Invalid syntax. \nSyntax: ```$$richest```"

        await ctx.reply(err_message)

    @syntax.error
    async def syntax_error(self, ctx, error):
        await ctx.reply("Somehow, you mistyped the most basic command. Just send the message ```$$syntax```")


class AdminCommands(commands.Cog):
    """Commands only admins have the power to do"""

    @commands.command()
    async def admin_give(self, ctx, val):
        """Allows admins to give money endlessly"""

        if not started:
            await ctx.reply("$$ not started")
            return
        else:
            print("$ has started")
        if not ctx.message.author.guild_permissions.administrator:
            await ctx.reply("Not an admin")
            return
        else:
            print("is an admin")

        if val.startswith("$"):
            val = val[1:]
        gift_val = int(val)

        giver = ctx.message.author

        recipients = []
        recipient_str = []

        for recipient in ctx.message.mentions:
            recipients.append(recipient.id)
            recipient_str.append(str(recipient.mention))

        recipients_wallet = {}
        for recipient in recipients:
            recipients_wallet[recipient] = (wallets[recipient] + gift_val)

        if len(recipient_str) == 1:
            each = ""
        else:
            each = " each"

        message = await ctx.channel.send("%s gave %s $%d%s for free."
                                         "\n\nReact to this message with :thumbsup: to confirm or :x: to cancel."
                                         % (giver.mention, ', '.join(recipient_str), gift_val, each))

        await message.add_reaction("👍")
        await message.add_reaction("❌")

        global confirmed
        confirmed = False

        def check(confirmation_emoji, user):

            print("checking")
            global confirmed
            confirmed = str(confirmation_emoji.emoji) == "👍"

            return confirmation_emoji.message == message and user == giver and \
                   (str(confirmation_emoji.emoji) == "👍" or str(confirmation_emoji.emoji) == "❌")

        await bot.wait_for('reaction_add', check=check)

        if confirmed:
            for recipient in recipients:
                wallets[recipient] = recipients_wallet[recipient]

            for member in ctx.guild.members:
                try:
                    await member.edit(nick=(everyones_names[member.id] + " {$%d}" % wallets[member.id]))
                    print(everyones_names[member.id] + " {$%d}" % wallets[member.id])
                except discord.errors.HTTPException:
                    print("Nick too long or is owner")
                    pass

            await ctx.channel.send("Confirmed.")
        else:
            await ctx.channel.send("Canceled.")

    @commands.command()
    async def start(self, ctx, val):
        """Begins $$ (and can only be done by admin)"""
        global started, initial_val, everyones_names

        if started:
            await ctx.reply("$$ already started")
            return
        if ctx.message.author.guild_permissions.administrator:
            if val.startswith("$"):
                val = val[1:]

            try:
                int_val = int(val)
            except ValueError:
                await ctx.reply("Not an integer. \nNotation: '$$start xx'")
                return

            for member in ctx.guild.members:
                wallets[member.id] = int_val
                if member.nick is None:
                    everyones_names[member.id] = member.name
                else:
                    everyones_names[member.id] = member.nick
            await ctx.channel.send("Gave @everyone $%d. \nEnjoy!!" % int_val)

            initial_val = int_val
            started = True

            for member in ctx.guild.members:
                try:
                    await member.edit(nick=(everyones_names[member.id] + " {$%d}" % wallets[member.id]))
                    print(everyones_names[member.id] + " {$%d}" % wallets[member.id])
                except discord.errors.HTTPException:
                    print("Nick too long or is owner")
                    pass
        else:
            await ctx.channel.send("You, %s, don't have permissions to "
                                   "do that. Contact an admin." % ctx.message.author.mention)

    @start.error
    async def start_error(self, ctx, error):
        err_message = "Invalid syntax. \nSyntax: $$start [money to give everyone]"

        # if isinstance(error, commands.BadArgument):
        #     err_message = "Invalid syntax. \nSyntax: $$start xx"
        # if isinstance(error, commands.BadArgument):
        #     err_message = "Invalid syntax. \nSyntax: $$start xx"
        # if isinstance(error, commands.BadArgument):
        #     err_message = "Invalid syntax. \nSyntax: $$start xx"
        # if isinstance(error, commands.errors.CommandInvokeError):
        #     print("Nick too long")
        #     return

        await ctx.reply(err_message)

    @admin_give.error
    async def admin_give_error(self, ctx, error):
        err_message = "Invalid syntax. \nSyntax: $$give [gift amount] @user (@user2 @user etc.) " \
                      "\n\n(And only admins can do it)"

        # if isinstance(error, commands.BadArgument):
        #     err_message = "Invalid syntax. \nSyntax: $$start xx"
        # if isinstance(error, commands.BadArgument):
        #     err_message = "Invalid syntax. \nSyntax: $$start xx"
        # if isinstance(error, commands.BadArgument):
        #     err_message = "Invalid syntax. \nSyntax: $$start xx"
        # if isinstance(error, commands.BadArgument):
        #     err_message = "Invalid syntax. \nSyntax: $$start xx"

        await ctx.reply(err_message)


class AuctionCommands(commands.Cog):
    """Commands for auctioning"""
    #                       0                          1             2            3     4
    # new_auction_entry = [ctx.message.author.id, highest bid, highest bidder.id, obj, True]

    @commands.command()
    async def auction(self, ctx, arg):
        """Auction off certain things. Only can be done by admin"""
        if not started:
            return

        if not ctx.message.author.guild_permissions.administrator:
            await ctx.reply("Not an admin")
            return

        obj = str(ctx.message.content[10:])
        new_auction_entry = [ctx.message.author.id, 0, None, obj, True]

        message = await ctx.channel.send("%s, do you really want to auction '%s'?"
                                         "\nReact with :thumbsup: to confirm or :x: to cancel"
                                         % (ctx.message.author.mention, obj))

        await message.add_reaction("👍")
        await message.add_reaction("❌")

        global confirmed
        confirmed = False

        def check(confirmation_emoji, user):

            print("checking")
            global confirmed
            confirmed = str(confirmation_emoji.emoji) == "👍"

            return confirmation_emoji.message == message and user == ctx.message.author and \
                   (str(confirmation_emoji.emoji) == "👍" or str(confirmation_emoji.emoji) == "❌")

        await bot.wait_for('reaction_add', check=check)

        if confirmed:

            await ctx.channel.send("Confirmed. Everyone, use $$bid [%d] [value] to bid for '%s'"
                                   "\n```THE AUCTION ID FOR THIS ITEM IS %d```"
                                   "\nExample: $$bid %d 100"
                                   "\n(bids $100 on this item)" % (len(auctions), obj, len(auctions), len(auctions)))
            auctions.append(new_auction_entry)
            print(auctions)
        else:
            await ctx.channel.send("Canceled.")

    @commands.command()
    async def bid(self, ctx, auction_index, val):
        if not started:
            return
        if val.startswith("$"):
            val = val[1:]
        bid_val = int(val)

        try:
            auction_index = int(auction_index)
            current_auction = auctions[auction_index]
        except Exception:
            err_msg = "Check that you are using the right auction ID. The available IDs are "
            i = 0
            for auction in auctions:
                if auction[4]:
                    err_msg += "%d for %s's %s" % (i, bot.get_user(auction[0]).mention, auction[3])
                i += 1
            await ctx.reply(err_msg)
            return

        if bid_val > wallets[ctx.message.author.id]:
            await ctx.reply("You don't have enough $$ for that.")
            return

        if bid_val <= current_auction[1]:
            await ctx.reply("You must bid higher than %d for %s's %s"
                            % (current_auction[1], bot.get_user(current_auction[0]).mention, current_auction[3]))
            return
        if not current_auction[4]:
            await ctx.reply("This item has already been sold.")
            return

        auctions[auction_index] = [current_auction[0], bid_val, ctx.message.author.id, current_auction[3], True]
        await ctx.channel.send("Accepted. The new highest bid for %s's %s is:"
                               "\n$%d" % (bot.get_user(current_auction[0]).mention, current_auction[3], bid_val))

    @commands.command()
    async def sold(self, ctx, auction_index):
        if not started:
            return
        try:
            auction_index = int(auction_index)
            current_auction = auctions[auction_index]
        except Exception:
            err_msg = "Check that you are using the right auction ID. The available IDs are "
            i = 0
            for auction in auction_index:
                if auction[4]:
                    err_msg += "%d for %s's %s" % (i, bot.get_user(auction[0]).mention, auction[3])
                i += 1
            await ctx.reply(err_msg)
            return

        if current_auction[0] != ctx.message.author.id:
            ctx.reply("You are not the auctioneer.")
        else:
            print(ctx.message.author.mention)
            print(bot.get_user(current_auction[2]).mention)

        message = await ctx.channel.send("%s, do you really want %s to be sold to %s for $%d?"
                                         "\nReact with :thumbsup: to confirm or :x: to cancel"
                                         % (ctx.message.author.mention, current_auction[3],
                                            bot.get_user(current_auction[2]).mention, current_auction[1]))

        await message.add_reaction("👍")
        await message.add_reaction("❌")

        global confirmed
        confirmed = False

        def check(confirmation_emoji, user):

            print("checking")
            global confirmed
            confirmed = str(confirmation_emoji.emoji) == "👍"

            return confirmation_emoji.message == message and user == ctx.message.author and \
                   (str(confirmation_emoji.emoji) == "👍" or str(confirmation_emoji.emoji) == "❌")

        await bot.wait_for('reaction_add', check=check)

        if confirmed:

            await ctx.channel.send("Confirmed. %s's %s is SOLD to %s for $%d"
                                   % (bot.get_user(current_auction[0]).mention, current_auction[3],
                                      bot.get_user(current_auction[2]).mention, current_auction[1]))
            auctions[auction_index][4] = False

            wallets[current_auction[0]] += current_auction[1]
            wallets[current_auction[2]] -= current_auction[1]
            print(auctions)
        else:
            await ctx.channel.send("Canceled.")

    @auction.error
    async def auction_error(self, ctx, error):
        await ctx.reply("Syntax error. Syntax: ```$$auction [thing to auction]```")

    @bid.error
    async def bid_error(self, ctx, error):
        await ctx.reply("Syntax error. Syntax: ```$$bid [auction id] [value]```"
                        "\nExample: $$bid 3 $200")

    @sold.error
    async def sold_error(self, ctx, error):
        await ctx.reply("Syntax error. Syntax: ```$$sold [auction id]```")


class BountyCommands(commands.Cog):
    """Commands for bounties"""
    #                       0                      1         2       3
    # new_bounty_entry = [ctx.message.author.id, amount, problem, active?]

    @commands.command()
    async def bounty(self, ctx, val):
        """Put bounties for challenge problems"""
        if not started:
            return

        val = int(val)

        prob = ctx.message.content[(10 + len(str(val))):]
        new_bounty_entry = [ctx.message.author.id, val, prob, True]

        if val > wallets[ctx.message.author.id]:
            await ctx.reply("Not enough $$")
            return

        message = await ctx.channel.send("%s, do you really want to put a bounty of $%d for this problem?"
                                         % (ctx.message.author.mention, val))

        await message.add_reaction("👍")
        await message.add_reaction("❌")

        global confirmed
        confirmed = False

        def check(confirmation_emoji, user):

            print("checking")
            global confirmed
            confirmed = str(confirmation_emoji.emoji) == "👍"

            return confirmation_emoji.message == message and user == ctx.message.author and \
                   (str(confirmation_emoji.emoji) == "👍" or str(confirmation_emoji.emoji) == "❌")

        await bot.wait_for('reaction_add', check=check)

        if confirmed:

            await ctx.channel.send("Confirmed. Everyone, the first to solve this problem: "
                                   "\n```%s```"
                                   "\ngets $%d!!"
                                   "\n(submit guesses by doing $$guess [bounty id] [guess])"
                                   "\nTHE BOUNTY ID FOR THIS PROBLEM IS **%d**"
                                   % (prob, val, len(bounties)))
            bounties.append(new_bounty_entry)
            print(bounties)
        else:
            await ctx.channel.send("Canceled.")

    @commands.command()
    async def guess(self, ctx, bounty_index):
        """Guess the answers to bounty problems"""
        if not started:
            return

        print(bounty_index)
        print(int(bounty_index))
        try:
            bounty_index = int(bounty_index)
            current_bounty = bounties[bounty_index]
        except Exception:
            err_msg = "Check that you are using the right bounty ID. The available IDs are "
            i = 0
            for bounty in bounties:
                if bounty[3]:
                    err_msg += "%d for %s's problem" % (i, bot.get_user(bounties[0]).mention)
                i += 1
            await ctx.reply(err_msg)
            return

        if not current_bounty[3]:
            await ctx.reply("This problem has already been solved.")
            return

        message = await ctx.channel.send("%s, is this correct?"
                                         % bot.get_user(current_bounty[0]).mention)

        await message.add_reaction("✅")
        await message.add_reaction("❌")

        global confirmed
        confirmed = False

        def check(confirmation_emoji, user):

            print("checking")
            global confirmed
            confirmed = str(confirmation_emoji.emoji) == "✅"

            return confirmation_emoji.message == message and user.id == current_bounty[0] and \
                   (str(confirmation_emoji.emoji) == "✅" or str(confirmation_emoji.emoji) == "❌")

        await bot.wait_for('reaction_add', check=check)

        if confirmed:
            bounties[bounty_index][3] = False
            await ctx.channel.send("Everyone, %s won the bounty for %s's problem (auction id %d)."
                                   "\nCongrats, %s"
                                   % (ctx.message.author.mention, bot.get_user(current_bounty[0]).mention,
                                   bounty_index, ctx.message.author.mention))
            print(bounties)
        else:
            await ctx.channel.send("Sorry, this is incorrect.")

    @bounty.error
    async def bounty_error(self, ctx, error):
        await ctx.reply("Syntax error. Syntax: ```$$bounty [value] [the actual problem]```")

    @guess.error
    async def guess_error(self, ctx, error):
        await ctx.reply("Syntax error. Syntax: ```$$guess [bounty id] [guess]```"
                        "\nExample: $$guess 3 42")


class Secret(commands.Cog):
    """shh 🤫"""
    @commands.command()
    async def theAnswer(self, ctx, guess):
        """shh don't tell anyone about this"""
        if guess == '42':
            ctx.reply("True!")
        else:
            ctx.reply("False.")

    @theAnswer.error
    async def theAnswer(self, ctx, error):
        pass


bot.add_cog(BasicCommands(bot))
bot.add_cog(AdminCommands(bot))
bot.add_cog(AuctionCommands(bot))
bot.add_cog(BountyCommands(bot))
bot.add_cog(Secret(bot))

token = ""
bot.run(token)
