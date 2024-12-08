import discord
from discord.ext import commands
from discord.ui import Button, View
import random
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 칩 데이터 저장
user_chips = {}

# 관리자 역할 ID 설정
ADMIN_ROLE_ID = 1315243698472091719  # 관리자의 역할 ID를 설정하세요

# 칩 지급 명령어
@bot.command()
async def 칩지급(ctx, member: discord.Member, amount: int):
    if not any(role.id == ADMIN_ROLE_ID for role in ctx.author.roles):
        await ctx.send("관리자만 사용할 수 있는 명령어입니다.")
        return
    if amount <= 0:
        await ctx.send("금액은 1 이상이어야 합니다.")
        return
    user_chips[member.id] = user_chips.get(member.id, 0) + amount
    embed = discord.Embed(title="칩 지급", description=f"{member.mention}님에게 {amount}칩을 지급했습니다.", color=discord.Color.green())
    await ctx.send(embed=embed)

# 칩 회수 명령어
@bot.command()
async def 칩회수(ctx, member: discord.Member, amount: int):
    if not any(role.id == ADMIN_ROLE_ID for role in ctx.author.roles):
        await ctx.send("관리자만 사용할 수 있는 명령어입니다.")
        return
    if amount <= 0 or user_chips.get(member.id, 0) < amount:
        await ctx.send("회수할 칩이 부족합니다.")
        return
    user_chips[member.id] -= amount
    embed = discord.Embed(title="칩 회수", description=f"{member.mention}님에게서 {amount}칩을 회수했습니다.", color=discord.Color.red())
    await ctx.send(embed=embed)

# 칩 초기화 명령어
@bot.command()
async def 칩초기화(ctx, member: discord.Member):
    if not any(role.id == ADMIN_ROLE_ID for role in ctx.author.roles):
        await ctx.send("관리자만 사용할 수 있는 명령어입니다.")
        return
    user_chips[member.id] = 0
    embed = discord.Embed(title="칩 초기화", description=f"{member.mention}님의 칩을 초기화했습니다.", color=discord.Color.blue())
    await ctx.send(embed=embed)

# 잔액 확인 명령어
@bot.command()
async def 잔액(ctx, member: discord.Member = None):
    if member:
        if not any(role.id == ADMIN_ROLE_ID for role in ctx.author.roles):
            await ctx.send("다른 사용자의 잔액은 관리자만 확인할 수 있습니다.")
            return
        chips = user_chips.get(member.id, 0)
        embed = discord.Embed(title="잔액 확인", description=f"{member.mention}님의 잔액은 {chips}칩입니다.", color=discord.Color.gold())
    else:
        chips = user_chips.get(ctx.author.id, 0)
        embed = discord.Embed(title="잔액 확인", description=f"{ctx.author.mention}님의 잔액은 {chips}칩입니다.", color=discord.Color.green())
    await ctx.send(embed=embed)

# 블랙잭 게임
@bot.command()
async def 블랙잭(ctx, amount: int):
    if amount <= 0 or user_chips.get(ctx.author.id, 0) < amount:
        await ctx.send("칩이 부족하거나 잘못된 금액입니다.")
        return

    user_chips[ctx.author.id] -= amount

    cards = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10}
    card_symbols = ["♠️", "♥️", "♦️", "♣️"]
    deck = [f"{symbol}{value}" for symbol in card_symbols for value in cards.keys()]
    user_hand = random.sample(deck, 2)
    bot_hand = random.sample(deck, 2)

    def calculate_score(hand):
        score = 0
        for card in hand:
            # 카드에서 숫자만 추출
            value = ''.join(filter(str.isdigit, card))  # 숫자만 필터링
            if not value:  # A, K, Q, J 등을 처리
                value = card[1:]
            score += cards.get(value, 0)  # 카드 딕셔너리에서 점수 가져오기
        return score

    user_score = calculate_score(user_hand)

    embed = discord.Embed(
        title="블랙잭 게임",
        description=f"**{ctx.author.mention}의 카드**: {', '.join(user_hand)} (점수: {user_score})\n**봇의 카드**: {bot_hand[0]}, [???]",
        color=discord.Color.gold()
    )
    embed.add_field(name="베팅 금액", value=f"{amount}칩", inline=False)
    embed.set_footer(text=f"현재 잔액: {user_chips.get(ctx.author.id, 0)}칩")

    view = View()
    hit_button = Button(label="카드 더 받기", style=discord.ButtonStyle.green)
    stand_button = Button(label="스탑", style=discord.ButtonStyle.red)

    async def hit_callback(interaction: discord.Interaction):
        nonlocal user_hand, user_score
        if interaction.user != ctx.author:
            await interaction.response.send_message("이 게임의 플레이어가 아닙니다.", ephemeral=True)
            return
        new_card = random.choice(deck)
        user_hand.append(new_card)
        user_score = calculate_score(user_hand)

        embed.description = f"**{ctx.author.mention}의 카드**: {', '.join(user_hand)} (점수: {user_score})\n**봇의 카드**: {bot_hand[0]}, [???]"

        if user_score > 21:
            embed.description += "\n\n**21점을 초과하여 패배했습니다!**"
            embed.add_field(name="획득 또는 손실", value=f"-{amount}칩", inline=False)
            embed.set_footer(text=f"현재 잔액: {user_chips.get(ctx.author.id, 0)}칩")
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            await interaction.response.edit_message(embed=embed, view=view)

    async def stand_callback(interaction: discord.Interaction):
        nonlocal user_score, bot_hand
        if interaction.user != ctx.author:
            await interaction.response.send_message("이 게임의 플레이어가 아닙니다.", ephemeral=True)
            return

        bot_score = calculate_score(bot_hand)
        while bot_score < 17:
            new_card = random.choice(deck)
            bot_hand.append(new_card)
            bot_score = calculate_score(bot_hand)

        if user_score > 21:
            result = "패배"
        elif bot_score > 21 or user_score > bot_score:
            result = "승리"
            user_chips[ctx.author.id] += amount * 2
        elif user_score == bot_score:
            result = "무승부"
            user_chips[ctx.author.id] += amount
        else:
            result = "패배"

        reward = amount * 2 if result == "승리" else 0
        embed.description = (
            f"**{ctx.author.mention}의 카드**: {', '.join(user_hand)} (점수: {user_score})\n"
            f"**봇의 카드**: {', '.join(bot_hand)} (점수: {bot_score})\n\n결과: {result}"
        )
        embed.add_field(name="획득 또는 손실", value=f"{reward - amount}칩", inline=False)
        embed.set_footer(text=f"현재 잔액: {user_chips.get(ctx.author.id, 0)}칩")
        await interaction.response.edit_message(embed=embed, view=None)

    hit_button.callback = hit_callback
    stand_button.callback = stand_callback
    view.add_item(hit_button)
    view.add_item(stand_button)

    await ctx.send(embed=embed, view=view)

# 바카라 게임
@bot.command()
async def 바카라(ctx, amount: int):
    if amount <= 0 or user_chips.get(ctx.author.id, 0) < amount:
        await ctx.send("칩이 부족하거나 잘못된 금액입니다.")
        return

    user_chips[ctx.author.id] -= amount

    embed = discord.Embed(title="바카라 게임", description="플레이어 또는 뱅커에 베팅하세요!", color=discord.Color.blue())
    view = View()

    player_button = Button(label="플레이어", style=discord.ButtonStyle.green)
    banker_button = Button(label="뱅커", style=discord.ButtonStyle.red)

    async def player_callback(interaction: discord.Interaction):
        if interaction.user != ctx.author:
            await interaction.response.send_message("이 게임의 플레이어가 아닙니다.", ephemeral=True)
            return
        result = random.choice(["플레이어", "뱅커"])
        win = result == "플레이어"
        reward = amount * 2 if win else 0
        user_chips[ctx.author.id] += reward
        embed.description = f"결과: **{result}**\n승패: {'승리' if win else '패배'}\n베팅 금액: {amount}칩\n획득 금액: {reward}칩"
        embed.set_footer(text=f"현재 잔액: {user_chips.get(ctx.author.id, 0)}칩")
        await interaction.response.edit_message(embed=embed, view=None)

    async def banker_callback(interaction: discord.Interaction):
        if interaction.user != ctx.author:
            await interaction.response.send_message("이 게임의 플레이어가 아닙니다.", ephemeral=True)
            return
        result = random.choice(["플레이어", "뱅커"])
        win = result == "뱅커"
        reward = amount * 2 if win else 0
        user_chips[ctx.author.id] += reward
        embed.description = f"결과: **{result}**\n승패: {'승리' if win else '패배'}\n베팅 금액: {amount}칩\n획득 금액: {reward}칩"
        embed.set_footer(text=f"현재 잔액: {user_chips.get(ctx.author.id, 0)}칩")
        await interaction.response.edit_message(embed=embed, view=None)

    player_button.callback = player_callback
    banker_button.callback = banker_callback

    view.add_item(player_button)
    view.add_item(banker_button)

    await ctx.send(embed=embed, view=view)
    
access_token = os.environ["BOT_token"]
bot.run(access_token)
