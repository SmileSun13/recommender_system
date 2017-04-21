import psycopg2
from math import sqrt
from time import *

connect = psycopg2.connect(database='movie_base', user='admin', host='localhost', password='admin')
cursor = connect.cursor()

def pearson_correlation(movie1, movie2):
	cursor.execute("SELECT rt1.rating, rt2.rating FROM ratings rt1 JOIN ratings rt2 ON rt1.user_id = rt2.user_id "
				   "WHERE rt1.movie_id = {} "
				   "AND rt2.movie_id = {};".format(movie1, movie2))
	rates_movies = cursor.fetchall()
	n = len(rates_movies)
	if n == 0:
		return 0
	sum1 = sum([x[0] for x in rates_movies])
	sum2 = sum([y[1] for y in rates_movies])
	sum1_square = sum([pow(x[0], 2) for x in rates_movies])
	sum2_square = sum([pow(y[1], 2) for y in rates_movies])
	product_sum = sum([xy[0] * xy[1] for xy in rates_movies])
	numerator = n * product_sum - sum1 * sum2
	denominator = sqrt((n * sum1_square - pow(sum1, 2)) * (n * sum2_square - pow(sum2, 2)))
	if denominator == 0:
		return 0
	return numerator / denominator

def best_matches(movies, movie, similarity = pearson_correlation):
	t1 = time()
	scores = [(similarity(movie, other_movie), other_movie) for other_movie in movies if other_movie != movie and movie < other_movie]
	scores.sort()
	scores.reverse()
	res  = [score for score in scores if score[0] > 0]
	res = res[:10]
	t2 = time()
	print(t2-t1)
	return res

def find_similar_movies():
	cursor.execute("SELECT movie_id FROM movies;")
	movies = [it[0] for it in cursor.fetchall()]
	c = 0
	for movie in movies:
		c += 1
		print(c)
		if c % 100 == 0:
			print("'%s' / '%s'" % (c, len(movies)))
		scores = best_matches(movies, movie)
		for rate, similar_movie in scores:
			cursor.execute("INSERT INTO similar_movies(movie1_id, movie2_id, similarity) VALUES({}, {}, {});".format(movie, similar_movie, rate))
		connect.commit()

find_similar_movies()

connect.close()