blocks.txt:
	python census2text.py -g block -s California -b 37.839072 -122.527084 37.694688 -122.167282 -v -w -o blocks.txt P7 P12 P26

tracts.txt:
	python census2text.py -g tract -s California -b 37.839072 -122.527084 37.694688 -122.167282 -v -w -o tracts.txt P7 P12 P26

zips.txt:
	python census2text.py -g zip -s California -b 37.839072 -122.527084 37.694688 -122.167282 -v -w -o zips.txt P7 P12 P26

counties.txt:
	python census2text.py -g county -v -w -o counties.txt P7 P12 P26
