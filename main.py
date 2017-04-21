import sys
from gui import *
from PyQt5 import QtWidgets
import psycopg2

connect = psycopg2.connect(database='movie_base', user='postgres', host='localhost', password='admin')
cursor = connect.cursor()


class MyWin(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.toolbutton_add_score.clicked.connect(self.add_score_field)
        self.ui.pushbutton_add_scores.clicked.connect(self.add_scores)
        self.ui.pushbutton_get_recommendations.clicked.connect(self.get_recommendations)
        self.ui.lineedit_input_movie.textChanged.connect(self.autocomplete)
        self.score_fields = []


    def add_scores(self):
        name = self.ui.lineedit_input_username.text()
        movie = self.ui.lineedit_input_movie.text()
        if name == "" or movie == "":
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Заполните пустые поля", QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            return
        cursor.execute("SELECT * FROM users WHERE name = {!r};".format(name))
        user_id = cursor.fetchone()
        if user_id is None:
            answer = QtWidgets.QMessageBox.question(self, "Не найден пользователь", "Добавить нового пользователя в базу?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                           QtWidgets.QMessageBox.Yes)
            if answer == QtWidgets.QMessageBox.Yes:
                cursor.execute("SELECT COUNT(*) FROM users;")
                c = cursor.fetchone()
                cursor.execute("ALTER SEQUENCE users_user_id_seq RESTART WITH {};".format(c[0] + 1,))
                connect.commit()
                cursor.execute("INSERT INTO users(name) VALUES({!r});".format(name))
                connect.commit()
            else:
                return
        cursor.execute("SELECT * FROM users WHERE name = {!r};".format(name))
        user_id = cursor.fetchone()[0]
        cursor.execute("SELECT movie_id FROM movies WHERE title = {!r};".format(movie))
        movie_id = cursor.fetchone()
        if movie_id is None:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Такого фильма не существует в базе", QtWidgets.QMessageBox.Ok,
                                          QtWidgets.QMessageBox.Ok)
            return
        temp = 0
        found = False
        for i in range(self.ui.layout_frame_movies_scores.count()):
            item = self.ui.layout_frame_movies_scores.itemAt(i)
            if i % 2 == 0:
                cursor.execute("SELECT movie_id FROM movies WHERE title = {!r};".format(item.widget().text()))
                temp = cursor.fetchone()[0]
                cursor.execute("SELECT * FROM ratings WHERE user_id = {} AND movie_id = {};".format(user_id, temp))
                it = cursor.fetchone()
                if it is not None:
                    found = True
            else:
                if found:
                    cursor.execute("UPDATE ratings SET rating = {} WHERE user_id = {} AND movie_id = {};".format(item.widget().value(), user_id, temp))
                else:
                    cursor.execute("INSERT INTO ratings(user_id, movie_id, rating) VALUES({}, {}, {});".format(user_id, temp, item.widget().value()))
        connect.commit()
        QtWidgets.QMessageBox.information(self, "Подтверждение", "Оценки успешно занесены в базу",
                                          QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
        for i in reversed(range(2, self.ui.layout_frame_movies_scores.count())):
            self.ui.layout_frame_movies_scores.itemAt(i).widget().setParent(None)
        self.ui.lineedit_input_movie.clear()
        self.ui.doublespinbox_input_score.clear()

    def get_recommendations(self):
        table = self.ui.tablewidget_get_recommendations
        for row in reversed(range(table.rowCount())):
            table.removeRow(row)
        user_name = self.ui.lineedit_input_username_2.text()
        if user_name == "":
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите имя пользователя", QtWidgets.QMessageBox.Ok,
                                          QtWidgets.QMessageBox.Ok)
            return
        cursor.execute("SELECT user_id FROM users WHERE name = {!r};".format(user_name))
        user = cursor.fetchone()
        if user is None:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Пользователя с таким именем не существует в базе",
                                          QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        user = user[0]
        n = self.ui.spinbox_number_of_recommendations.value()
        if n == 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите желаемое количество рекомендаций",
                                          QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return
        cursor.execute("SELECT movie_id, rating FROM ratings WHERE user_id = {};".format(user))
        user_ratings = dict(cursor.fetchall())
        scores = {}
        sum_similarity = {}
        for movie, rating in user_ratings.items():
            #cursor.execute("SELECT movie2_id, similarity FROM similar_movies WHERE movie1_id = {};".format(movie))
            cursor.execute("SELECT movie1_id, movie2_id, similarity FROM similar_movies WHERE movie1_id = {} OR movie2_id = {};".format(movie, movie))
            #similar_movies = cursor.fetchall()
            temp = cursor.fetchall()
            similar_movies = []
            for it in temp:
                if it[0] != movie:
                    similar_movies.append((it[0], it[2]))
                else:
                    similar_movies.append((it[1], it[2]))
            for similar_movie, similarity in similar_movies:
                if similar_movie in user_ratings:
                    continue
                scores.setdefault(similar_movie, 0)
                scores[similar_movie] += similarity * rating
                sum_similarity.setdefault(similar_movie, 0)
                sum_similarity[similar_movie] += similarity
        ratings = [(score / sum_similarity[movie], movie) for movie, score in scores.items()]
        if len(ratings) < n:
            cursor.execute("SELECT average_rating, movie_id FROM movies WHERE count_rated >= 100 ORDER BY average_rating DESC LIMIT {};".format(n - len(ratings)))
            it = cursor.fetchall()
            ratings += it
        ratings.sort()
        ratings.reverse()
        ratings = ratings[:n]
        for i, j in ratings:
            cursor.execute("SELECT title FROM movies WHERE movie_id = {};".format(j))
            movie_title = cursor.fetchone()[0]
            row_pos = self.ui.tablewidget_get_recommendations.rowCount()
            self.ui.tablewidget_get_recommendations.insertRow(row_pos)
            self.ui.tablewidget_get_recommendations.setItem(row_pos, 0, QtWidgets.QTableWidgetItem(movie_title))
            self.ui.tablewidget_get_recommendations.setItem(row_pos, 1, QtWidgets.QTableWidgetItem(str(i)))

    def autocomplete(self):
        cursor.execute("SELECT title FROM movies WHERE title LIKE '%%' || %s || '%%';", (self.sender().text(),))
        it = cursor.fetchall()
        strings = [item[0] for item in it]
        completer = QtWidgets.QCompleter(strings, self)
        self.sender().setCompleter(completer)
        self.sender().show()

    def add_score_field(self):
        r = self.ui.layout_frame_movies_scores.rowCount()
        if r == 25:
            return
        new_lineedit = QtWidgets.QLineEdit(self.ui.frame_movies_scores)
        new_lineedit.setObjectName("lineedit_input_movie")
        self.score_fields.append(new_lineedit)
        self.ui.layout_frame_movies_scores.addWidget(new_lineedit, r, 0)
        new_lineedit.textChanged.connect(self.autocomplete)
        self.doublespinbox_input_score = QtWidgets.QDoubleSpinBox(self.ui.frame_movies_scores)
        self.doublespinbox_input_score.setObjectName("doublespinbox_input_score")
        self.doublespinbox_input_score.setSingleStep(0.5)
        self.doublespinbox_input_score.setRange(0.5, 5.0)
        self.doublespinbox_input_score.setDecimals(1)
        self.ui.layout_frame_movies_scores.addWidget(self.doublespinbox_input_score, r, 1)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    myapp = MyWin()
    myapp.show()
    sys.exit(app.exec_())


connect.close()