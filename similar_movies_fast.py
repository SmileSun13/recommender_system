from math import sqrt
import psycopg2
from time import *

userPrefs = {}
prefs = {}
movies = {}
itemMatch = {}

#connect = psycopg2.connect(database='movie_base', user='admin', host='localhost', password='admin')
#cursor = connect.cursor()

def loadMovieLens(path='/home/smilesun/PycharmProjects/recommender_system'):
	for line in open(path+'/movies.csv'):
		(id,title)=line.split(';')[0:2]
		movies[id]=title
	for line in open(path+'/ratings.csv'):
		(user,movieid,rating)=line.split(',')
		userPrefs.setdefault(user,{})
		userPrefs[user][movieid] = float(rating)
		prefs.setdefault(movieid,{})
		prefs[movieid][user]=float(rating)

loadMovieLens()

def sim_pearson(p1,p2):
	si={}
	for item in prefs[p1]:
		if item in prefs[p2]:
			si[item]=1
	n=len(si)
	if n==0:
		return 0
	sum1=sum([prefs[p1][it] for it in si])
	sum2=sum([prefs[p2][it] for it in si])
	sum1Sq=sum([pow(prefs[p1][it],2) for it in si])
	sum2Sq=sum([pow(prefs[p2][it],2) for it in si])
	pSum=sum([prefs[p1][it]*prefs[p2][it] for it in si])
	num=pSum-(sum1*sum2/n)
	den=sqrt((sum1Sq-pow(sum1,2)/n)*(sum2Sq-pow(sum2,2)/n))
	if den==0:
		return 0
	r=num/den
	return r

def topMatches(movie,similarity=sim_pearson):
	#scores=[(similarity(movie,other),other) for other in prefs if other!=movie]
	scores = [(similarity(movie, other_movie), other_movie) for other_movie in prefs if other_movie != movie and movie < other_movie]
	scores.sort()
	scores.reverse()
	res  = [scores[i] for i in range(min(11, len(scores))) if scores[i][0] > 0]
	return res

def find_similar_movies(connect, cursor):
	c=0
	t1 = time()
	for item in prefs:
		c+=1
		if c%100==0:
			print("%d / %d" % (c,len(prefs)))
			t2 = time()
			#print(t2 - t1)
		scores=topMatches(item)
		for rate, similar_movie in scores:
			cursor.execute("INSERT INTO similar_movies(movie1_id, movie2_id, similarity) VALUES({}, {}, {});".format(item, similar_movie, rate))
		connect.commit()

#find_similar_movies()

#connect.close()