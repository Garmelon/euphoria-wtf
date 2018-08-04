import asyncio
import configparser
import logging
import re

import yaboli
from yaboli.utils import *


logger = logging.getLogger("wtf")

class WtfDB(yaboli.Database):
	def initialize(self, db):
		with db:
			db.execute((
				"CREATE TABLE IF NOT EXISTS acronyms ("
					"acronym_id INTEGER PRIMARY KEY, "
					"acronym TEXT NOT NULL, "
					"explanation TEXT NOT NULL, "
					"author TEXT NOT NULL, "
					"deleted BOOLEAN NOT NULL DEFAULT 0"
				")"
			))
			db.create_function("p_lower", 1, str.lower)

	@yaboli.operation
	def add(self, db, acronym, explanation, author):
		with db:
			db.execute((
				"INSERT INTO acronyms (acronym, explanation, author) "
				"VALUES (?,?,?)"
			), (acronym, explanation, author))
	
	@yaboli.operation
	def find(self, db, acronym):
		c = db.execute((
			"SELECT acronym, explanation FROM acronyms "
			"WHERE NOT deleted AND p_lower(acronym) = ?"
		), (acronym.lower(),))
		return c.fetchall()

	@yaboli.operation
	def find_full(self, db, acronym):
		c = db.execute((
			"SELECT acronym_id, acronym, explanation, author FROM acronyms "
			"WHERE NOT deleted AND p_lower(acronym) = ?"
		), (acronym.lower(),))
		return c.fetchall()

	@yaboli.operation
	def delete(self, db, acronym_id):
		with db:
			db.execute("UPDATE acronyms SET deleted = 1 WHERE acronym_id = ?", (acronym_id,))

class Wtf:
	SHORT_DESCRIPTION = "A database of explanations for words, acronyms and initialisms"
	DESCRIPTION = (
		"'wtf' is a database of explanations for words, acronyms and initialisms."
		" It is inspired by the linux wtf program and uses its acronyms,"
		" in addition to ones set by users.\n"
	)
	COMMANDS = (
		"!wtf is <term> - look up a term\n"
		"!wtf add <term> <explanation> - add a new explanation\n"
		"!wtf detail <term> - shows more info about the term's explanations\n"
		"!wtf delete <id> - delete explanation with corresponding id (look up the id using !wtf detail)\n"
	)
	CREDITS = "Created by @Garmy using github.com/Garmelon/yaboli\n"

	RE_IS     = r"\s*is\s+(\S+)\s*"
	RE_ADD    = r"\s*add\s+(\S+)\s+(.*)"
	RE_DETAIL = r"\s*detail\s+(\S+)\s*"
	RE_DELETE = r"\s*delete\s+(\d+)\s*"

	def __init__(self, dbfile):
		self.db = WtfDB(dbfile)
	
	@yaboli.command("wtf")
	async def command_wtf(self, room, message, argstr):
		match_is     = re.fullmatch(self.RE_IS,     argstr)
		match_add    = re.fullmatch(self.RE_ADD,    argstr)
		match_detail = re.fullmatch(self.RE_DETAIL, argstr)
		match_delete = re.fullmatch(self.RE_DELETE, argstr)

		if match_is:
			acronym = match_is.group(1)
			explanations = await self.db.find(acronym)
			if explanations:
				# Acronym, Explanation
				lines = [f"{a} — {e}" for a, e in explanations]
				text = "\n".join(lines)
				await room.send(text, message.mid)
			else:
				await room.send(f"{acronym!r} not found.", message.mid)

		elif match_add:
			acronym = match_add.group(1)
			explanation = match_add.group(2).strip()
			await self.db.add(acronym, explanation, message.sender.nick)
			await room.send(f"Added explanation: {acronym} — {explanation}", message.mid)
			logger.INFO(f"{mention(message.sender.nick)} added explanation: {acronym} - {explanation}")

		elif match_detail:
			acronym = match_detail.group(1)
			explanations = await self.db.find_full(acronym)
			if explanations:
				# Id, Acronym, Explanation, aUthor
				lines = [f"{i}: {a} — {e} (by {mention(u, ping=False)})" for i, a, e, u in explanations]
				text = "\n".join(lines)
				await room.send(text, message.mid)
			else:
				await room.send(f"{acronym!r} not found.", message.mid)

		elif match_delete:
			aid = match_delete.group(1)
			await self.db.delete(aid)
			await room.send(f"Deleted.", message.mid)
			logger.INFO(f"{mention(message.sender.nick)} deleted explanation with id {aid}")

		else:
			text = "Usage:\n" + self.COMMANDS
			await room.send(text, message.mid)

class WtfBot(yaboli.Bot):
	SHORT_HELP = Wtf.SHORT_DESCRIPTION
	LONG_HELP = Wtf.DESCRIPTION + Wtf.COMMANDS + Wtf.CREDITS

	def __init__(self, nick, wtfdbfile, cookiefile=None):
		super().__init__(nick, cookiefile=cookiefile)
		self.wtf = Wtf(wtfdbfile)

	async def on_command_specific(self, room, message, command, nick, argstr):
		if similar(nick, room.session.nick) and not argstr:
			await self.botrulez_ping(room, message, command)
			await self.botrulez_help(room, message, command, text=self.LONG_HELP)
			await self.botrulez_uptime(room, message, command)
			await self.botrulez_kill(room, message, command)
			await self.botrulez_restart(room, message, command)

	async def on_command_general(self, room, message, command, argstr):
		if not argstr:
			await self.botrulez_ping(room, message, command)
			await self.botrulez_help(room, message, command, text=self.SHORT_HELP)

		await self.wtf.command_wtf(room, message, command, argstr)

def main(configfile):
	logging.basicConfig(level=logging.INFO)

	config = configparser.ConfigParser(allow_no_value=True)
	config.read(configfile)

	nick = config.get("general", "nick")
	cookiefile = config.get("general", "cookiefile", fallback=None)
	wtfdbfile = config.get("general", "wtfdbfile", fallback=None)
	bot = WtfBot(nick, wtfdbfile, cookiefile=cookiefile)

	for room, password in config.items("rooms"):
		if not password:
			password = None
		bot.join_room(room, password=password)

	asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
	main("wtf.conf")
