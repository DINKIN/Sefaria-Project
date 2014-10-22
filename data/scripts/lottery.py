from random import randrange

points = {
	"ira pollack": 16362,
	"Aryeh S": 8497,
	"Naftali Wolfe": 7924,
	"Joshua Kulp": 6781,
	"Arie Schwartz": 4870,
	"Eli Friedman": 3359,
	"Elli Fischer": 2841,
	"Jared Anstandig": 2665,
	"Katie Kroik": 2493,
	"Sarah Brodsky": 2434,
	"Adir Yolkut": 2330,
	"Isaac Moses": 2284,
	"Jonathan Seligsohn": 2254,
	"Michael Hamm": 2231,
	"Elisheva Urbas": 2057,
	"William Friedman": 1875,
	"Ilan Griboff": 1556,
	"Noah Santacruz": 1383,
	"Jeremy Markiz": 1223,
	"Yonatan Milevsky": 1189,
	"Jonathan Baker": 951,
	"yoni spero": 846,
	"Alan Nochenson": 809,
	"Dani Ungar": 718,
	"Amir Karger": 540,
	"max nesser": 463,
	"Elisha Paul": 374,
	"Yehoshua L": 357,
	"hallel kula": 349,
	"Stephanie Pell": 322,
	"Philip Gibbs": 292,
	"Rivka Hia": 290,
	"Brian Schneider": 274,
	"Goldi Kozloski": 255,
	"Yitzchak Friedman": 236,
	"Eli Duker": 227,
	"Elazar Hirsch": 223,
	"Raphael Magarik": 223,
	"elliot kaplowitz": 218,
	"Joel Dinin": 214,
	"Michael Kopinsky": 202,
	"Sam Goldberg": 199,
	"Ari Elias-Bachrach": 193,
	"Susann Codish": 166,
	"Drew Kaplan": 154,
	"Yoni Kornblau": 151,
	"Yehuda Faguet": 148,
	"Benny Hutman": 138,
	"David Pardo": 135,
	"Amir Zinkow": 132,
	"Yakov Smith": 132,
	"Asher Apsan": 129,
	"Ari Heitner": 127,
	"Moshe Farkas": 123,
	"David Kominsky": 122,
	"Jennifer Seligman": 119,
	"Avrohom Kotler": 115,
	"Eytan Yammer": 104,
	"rivka efremenko": 104,
	"Shira Fischer": 99,
	"Yisrael Hollender": 96,
	"Nelly Altenburger": 95,
	"Josh Koperwas": 94,
	"Jeremy Szczepanski": 91,
	"Rabbi Simcha Daniel Burstyn": 80,
	"Netanel Paley": 76,
	"Ori Pomerantz": 66,
	"yisroel sufrin": 65,
	"Michael Sandler": 64,
	"shalom lipszyc": 63,
	"Eli L": 58,
	"Orrin Krublit": 50,
	"Benjamin Baruch": 47,
	"david strauss": 42,
	"Moshe Schorr": 41,
	"Abraham Kohen": 39,
	"Isaac Shalev": 37,
	"Isaac Hier": 35,
	"Rigel Janette": 31,
	"Mayer Kohn": 23,
	"eitan etz": 23,
	"naht anoj": 21,
	"Melissa Ser": 20,
	"Shmuel Cahn": 18,
	"Adam Ariel": 17,
	"Ezra HaLevi": 16,
	"Yosef Skolnick": 14,
	"Miriam Bensimon": 10,
	"David Avraham": 3,
}

discounts = {
	"Alan Nochenson": 0.3333333333,
	"Ari Elias-Bachrach": 0.6666666667,
	"Aryeh S": 0.6666666667,
	"eitan eitz": 0,
	"Elazar Hirsch": 0.3333333333,
	"Isaac Moses": 0.8333333333,
	"max nesser": 0.6666666667,
	"Mayer Kohn": 0,
	"naht anoj": 0,
	"Orrin Krublit": 0,
	"Philip Gibbs": 0.6666666667,
	"Rigel Janette": 0,
	"Shira Fischer": 0.5,
	"Susann Codish": 0.6666666667,
	"Yakov Smith": 0.6666666667,
	"yisroel sufrin": 0.3,
	"Yoni Kornblau": 0.6666666667,
}

for person in discounts:
	if person in points:
		points[person] = int(points[person] * discounts[person])

for i in range(18):
	total = sum(points.values())
	count = 0
	winner = randrange(total)
	for person in points:
		count += points[person]
		if count > winner:
			print "%d. %s" % (i+1, person)
			del points[person]
			break
