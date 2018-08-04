#!/bin/env python3

# A short script to import the wtf program's "databases" of acronyms.

import asyncio
import sys

import wtf


async def import_file(db, acronymfile):
	with open(acronymfile) as f:
		for line in f:
			s = line.split("\t", 1)
			if len(s) == 2:
				acronym, explanation = s
				explanation = explanation.strip()
				print(f"{acronym} - {explanation}")
				await db.add(acronym, explanation, "importer")

def main(dbfile, acronymfiles):
	db = wtf.WtfDB(dbfile)
	loop = asyncio.get_event_loop()

	for acronymfile in acronymfiles:
		loop.run_until_complete(import_file(db, acronymfile))

if __name__ == "__main__":
	if len(sys.argv) >= 3:
		main(sys.argv[1], sys.argv[2:])
	else:
		print("  USAGE:")
		print(f"{sys.argv[0]} <dbfile> <acronymfile> [<acronymfile> ...]")
		exit(1)
