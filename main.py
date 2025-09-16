from dotenv import load_dotenv
import discord  
from discord.ext import commands, tasks
import os
from flask import Flask
from threading import Thread


app = Flask('')

@app.route('/')
def home():
    return "Le bot est en ligne !"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()



###########################################                          
#                 MEHTODE                 #
###########################################
user_vocal_channels = {}

ID_SALON_MEMBRES = 1417326109980360884
ID_SALON_VOCAL = 1417326216620277922
ID_SALON_NOM_SERVEUR = 1417326990515634328

role_id = 1417281361127149642 


intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix="+", intents=intents)

###########################################                          
#             DEMARRAGE DU BOT            #
###########################################

@bot.event
async def on_ready():
    print(f"🔄 Mise à jour des statistiques en cours...")
    update_stats.start()
    print(f'{bot.user} est en ligne ✅')

    await bot.change_presence(activity=discord.Streaming(name="sur /Kawazu", url="https://twitch.tv/kawazu"))


###########################################                          
#             GESTION ERROR               #
###########################################

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 Tu n'as pas les permissions nécessaires pour faire ça.")
    
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❗ Il manque un argument dans ta commande.")

    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❓ Cette commande n'existe pas.")

    else:
        # Erreur inconnue → debug terminal
        await ctx.send("❌ Une erreur est survenue.")
        raise error  # Pour l'afficher dans la console
    
###########################################                          
#              COMMANDE LOCK              #
###########################################

@bot.command()
@commands.has_permissions(manage_channels=True)

async def lock(ctx):
    role = discord.utils.get(ctx.author.roles, id=role_id)
    if not role:
         await ctx.send("❌ Tu n'as pas le rôle requis pour utiliser cette commande.")
    else:
        try:
            overwrite = discord.PermissionOverwrite()
            overwrite.send_messages = False

            await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

            waiting_message = await ctx.send("🔒 Salon verrouillé !")
        except discord.Forbidden:
            await ctx.send("❗ Je n'ai pas la permission de modifier les permissions de ce salon.")

###########################################                          
#             COMMANDE UNLOCK             #
###########################################

@bot.command()
@commands.has_permissions(manage_channels=True)

async def unlock(ctx):
    role = discord.utils.get(ctx.author.roles, id=role_id)
    if not role:
         await ctx.send("❌ Tu n'as pas le rôle requis pour utiliser cette commande.")
    else:    
        try:
            overwrite = discord.PermissionOverwrite()
            overwrite.send_messages = True

            await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            waiting_message = await ctx.send("🔓 Salon déverrouillé !") 
            await waiting_message.delete(delay=5)   
        except discord.Forbidden:
            await ctx.send("❗ Je n'ai pas la permission de modifier les permissions de ce salon.")


############################################                        
#              COMMANDE CLEAR              #
############################################

@bot.command()
@commands.has_permissions(manage_messages=True)

async def clear(ctx, amount: int):
        try:
            await ctx.channel.purge(limit=amount)
            waiting_message = await ctx.send(f"🧹 {amount} messages supprimés !")
            await waiting_message.delete(delay=5)
        except discord.Forbidden:
            await ctx.send("❗ Je n'ai pas la permission de supprimer des messages dans ce salon.")

############################################                        
#          SYSTEM STATISTIQUE AUTO         #
############################################

@tasks.loop(minutes=1)  # met à jour toutes les 1 min
async def update_stats():
    guild = bot.guilds[0]  # le premier serveur où le bot est
    salon_membres = guild.get_channel(ID_SALON_MEMBRES)
    salon_vocal = guild.get_channel(ID_SALON_VOCAL)
    salon_nom = guild.get_channel(ID_SALON_NOM_SERVEUR)

    nb_membres = guild.member_count
    nb_vocaux = sum(1 for member in guild.members if member.voice and not member.bot)
    nom_serveur = guild.name

    await salon_membres.edit(name=f"🎭 > Membres : {nb_membres}")
    await salon_vocal.edit(name=f"🔊 > En vocal : {nb_vocaux}")
    await salon_nom.edit(name=f"⛩️ > {nom_serveur}")

@bot.event
async def on_voice_state_update(member, before, after):
    ID_SALON_CREATION = 1417357697812136057  # Remplace par ton salon de création

    # Il rejoint le salon de création
    if after.channel and after.channel.id == ID_SALON_CREATION:
        category = after.channel.category

        # Crée le salon vocal personnalisé
        overwrites = {
            member.guild.default_role: discord.PermissionOverwrite(connect=False),
            member: discord.PermissionOverwrite(connect=True, manage_channels=True)
        }

        vocal = await member.guild.create_voice_channel(
            name=f"🔊 {member.name}",
            overwrites=overwrites,
            category=category
        )

        # Déplace l’utilisateur dans le nouveau salon
        await member.move_to(vocal)

        # Sauvegarde le salon pour ce membre
        user_vocal_channels[member.id] = vocal.id
        # Quand un salon vocal est vide, on le supprime
    if before.channel and before.channel.id in user_vocal_channels.values():
        if len(before.channel.members) == 0:
            await before.channel.delete()


###########################################                          
#             COMMANDE LOCKVC             #
###########################################

@bot.command()
async def lockvc(ctx):
    channel_id = user_vocal_channels.get(ctx.author.id)
    if not channel_id:
        await ctx.send("❌ Tu ne possèdes pas de salon vocal personnel.")
        return

    channel = bot.get_channel(channel_id)
    if ctx.author not in channel.members:
        await ctx.send("❌ Tu dois être dans ton salon vocal pour le verrouiller.")
        return

    await channel.set_permissions(ctx.guild.default_role, connect=False)
    await ctx.send("🔒 Ton salon vocal est maintenant verrouillé.")

###########################################                          
#             COMMANDE UNLOCKVC           #
###########################################

@bot.command()
async def unlockvc(ctx):
    channel_id = user_vocal_channels.get(ctx.author.id)
    if not channel_id:
        await ctx.send("❌ Tu ne possèdes pas de salon vocal personnel.")
        return

    channel = bot.get_channel(channel_id)
    if ctx.author not in channel.members:
        await ctx.send("❌ Tu dois être dans ton salon vocal pour le déverrouiller.")
        return

    await channel.set_permissions(ctx.guild.default_role, connect=True)
    await ctx.send("🔓 Ton salon vocal est maintenant déverrouillé.")

keep_alive()
bot.run("")
