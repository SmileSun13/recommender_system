from similar_movies_fast import find_similar_movies
import psycopg2
from math import sqrt

connect = psycopg2.connect(database='movie_base', user='admin', host='localhost', password='admin')

def rmse():
    cursor = connect.cursor()
    cursor.execute("SELECT user_id FROM users ORDER BY random() LIMIT 1000;")
    users = cursor.fetchall()
    lst = {}
    for user in users:
        cursor.execute("SELECT movie_id, rating FROM ratings WHERE user_id = {} ORDER BY random() LIMIT 1;".format(user[0]))
        it = cursor.fetchone()
        if it is None:
            continue
        lst[user[0]] = it
        cursor.execute("DELETE FROM ratings WHERE user_id = {} AND movie_id = {};".format(user[0], it[0]))
    cursor.execute("TRUNCATE TABLE similar_movies CONTINUE IDENTITY RESTRICT;")
    connect.commit()
    find_similar_movies(connect, cursor)
    lst2 = {}
    for user, movie_score in lst.items():
        cursor.execute("SELECT movie1_id, movie2_id, similarity FROM similar_movies WHERE movie1_id = {} OR movie2_id = {};".format(movie_score[0], movie_score[0]))
        temp = cursor.fetchall()
        similar_movies = []
        for it in temp:
            if it[0] != movie_score[0]:
                similar_movies.append((it[0], it[2]))
            else:
                similar_movies.append((it[1], it[2]))
        sum_sim = 0
        sum_product = 0
        for similar_movie, similarity in similar_movies:
            cursor.execute("SELECT rating FROM ratings WHERE user_id = {} AND movie_id = {};".format(user, similar_movie))
            it = cursor.fetchone()
            if it is None:
                continue
            it = it[0]
            sum_sim += similarity
            sum_product += similarity * it
        if sum_sim != 0:
            score_predict = sum_product / sum_sim
        else:
            cursor.execute("SELECT rating FROM ratings WHERE movie_id = {};".format(movie_score[0],))
            scores = cursor.fetchall()
            if len(scores) > 0:
                score_predict = sum([score[0] for score in scores]) / len(scores)
            else:
                score_predict = 3.5
        lst2[user] = (movie_score[1], score_predict)
    s = 0
    for scores in lst2.values():
        s += (scores[0] - scores[1])**2
    s = sqrt(s / len(lst2))
    print(s)
    for user, movie_score in lst.items():
        cursor.execute("INSERT INTO ratings(user_id, movie_id, rating) VALUES({}, {}, {});".format(user, movie_score[0], movie_score[1]))
    connect.commit()

rmse()

connect.close()