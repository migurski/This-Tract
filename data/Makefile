CENSUS2TXT=~/Documents/Census/census2text.py

blocks.txt:
	python $(CENSUS2TXT) -g block -s California -b 37.839072 -122.527084 37.694688 -122.167282 -v -w -o blocks.txt P7 P12 P26

tracts.txt:
	python $(CENSUS2TXT) -g tract -s California -b 37.839072 -122.527084 37.694688 -122.167282 -v -w -o tracts.txt P7 P12 P26

zips.txt:
	python $(CENSUS2TXT) -g zip -s California -b 37.839072 -122.527084 37.694688 -122.167282 -v -w -o zips.txt P7 P12 P26

counties.txt:
	python $(CENSUS2TXT) -g county -v -w -o counties.txt P7 P12 P26

states.txt:
	python $(CENSUS2TXT) -g state -v -w -o states.txt P7 P12 P26
