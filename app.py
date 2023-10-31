######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

from datetime import datetime

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Ruihang2001'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	print('register')

	suppress = request.values.get("suppress")
	
	if suppress:
		return render_template('register.html', suppress=True)
	else:
		return render_template('register.html')


@app.route("/register", methods=['POST'])
def register_user():
	try:
		firstname = request.form.get('firstname')
		lastname = request.form.get('lastname')
		email=request.form.get('email')
		birthday = request.form.get('birthday')
		print("birthday = " + birthday)
		hometown = request.form.get('hometown')
		gender = request.form.get('gender')
		password=request.form.get('password')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)

	if test:

		if birthday:
			cursor.execute('''INSERT INTO Users (first_name, last_name, email, DOB, hometown, gender, password) 
		VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')'''.format(firstname, lastname, email, birthday, hometown, gender, password))
		else:
			cursor.execute('''INSERT INTO Users (first_name, last_name, email, DOB, hometown, gender, password) 
		VALUES ('{0}', '{1}', '{2}', NULL, '{3}', '{4}', '{5}')'''.format(firstname, lastname, email, hometown, gender, password))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!', allphotos=getAllUsersPhotos())
	else:
		print("Email not unique")
		return flask.redirect(flask.url_for('register', suppress=True))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute('''SELECT imgdata, picture_id, caption, A.aname, A.aid 
		FROM Album AS A, Pictures AS P 
		WHERE A.user_id = '{0}' AND A.aid = P.aid'''.format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption, A.aname, A.aid), ...]

def getAllUsersPhotos():
	cursor = conn.cursor()
	cursor.execute('''SELECT P.imgdata, P.picture_id, P.caption, U.email, U.user_id
		FROM Pictures AS P, Album AS A, Users AS U 
		WHERE P.aid = A.aid AND U.user_id = A.user_id''')
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption, email), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getUseremailFromid(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT email  FROM Users WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()[0]

def getLikes():
	cursor = conn.cursor()
	cursor.execute(""" SELECT picture_id, COUNT(user_id)
						FROM likes
						GROUP BY picture_id """)
	return cursor.fetchall()

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

# to get the top 10 contributors
def getTopContributor():
	cursor = conn.cursor()
	cursor.execute("SELECT email, contribution FROM Users ORDER BY contribution desc limit 10")
	return cursor.fetchall()

# to get the list of albums of the current user:
def getUsersAlbum(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT aid, aname FROM Album WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

# get the album id given the album name:
def getAlbumID(name):
	cursor = conn.cursor()
	cursor.execute("SELECT aid FROM Album WHERE aname = '{0}'".format(name))
	return cursor.fetchall()[0]

@app.route('/profile')
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('hello.html', 
							name=flask_login.current_user.id, 
							message="Here's your profile", 
							friends = getUsersFriendsEmail(uid),
							tags=getAllTags(),
							mostPopularTag=getMostPopularTag(),
							albums=getUsersAlbum(uid),
							userphotos=getUsersPhotos(uid),
							base64=base64)

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		aid = request.form.get('albums')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (aid, imgdata, caption) VALUES (%s, %s, %s )''', (aid, photo_data, caption))

		conn.commit()

		return gotoHelloPage("Photo uploaded!")
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		albumList = getUsersAlbum(uid)

		if len(albumList) != 0:
			return render_template('upload.html', albums = getUsersAlbum(uid))
		else:
			print("Album has nothing!!")
			return render_template('upload.html', albums = None)
#end photo uploading code

@app.route("/deletePhoto/<int:pid>")
@flask_login.login_required
def deletePhoto(pid):
	cursor = conn.cursor()
	cursor.execute('''DELETE FROM Pictures WHERE picture_id = '{0}' '''.format(pid))

	# uid = getUserIdFromEmail(flask_login.current_user.id)

	conn.commit()
	return gotoHelloPage("Photo deleted!")

@app.route("/deleteAlbum/<int:aid>")
@flask_login.login_required
def deleteAlbum(aid):
	try:
		cursor = conn.cursor()
		cursor.execute('''DELETE FROM Album WHERE aid = '{0}' '''.format(aid))
		conn.commit()
		return gotoHelloPage("Album deleted!") 
	except:
		print("fail to delete aid = " + str(aid))
		return gotoHelloPage("Album deletion unsuccessful") 

@app.route("/album", methods=['GET', 'POST'])
@flask_login.login_required
def createAlbum():
	if request.method == 'POST':
		print("creating the album in SQL")

		try:
			# Getting the name of the album
			name = request.form.get('aname')
			print("Got the name of the album: " + name)
		except:
			print("couldn't fetch album name ") #this prints to shell, end users will not see this (all print statements go to shell)
			return flask.redirect(flask.url_for('album'))
		
		# Getting the date for now:
		now = datetime.now()
		# Format date:
		formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')

		# Getting the current user id:
		uid = getUserIdFromEmail(flask_login.current_user.id)

		try:
			# Insert into the sql
			cursor = conn.cursor()
			print(cursor.execute('''INSERT INTO Album (aname, date_of_creation, user_id) 
				VALUES ('{0}', '{1}', '{2}')'''.format(name, formatted_date, uid)))
			conn.commit()
			
			return gotoHelloPage("Album Created!")
		except:
			return gotoHelloPage("You already have an album with the same name!")
	else:
		print('showing the page for Album creation')
		return render_template('createAlbum.html')

@app.route("/viewAlbum/<aid>", methods=["GET"])
@flask_login.login_required
def viewAlbum(aid):
	return render_template('viewByTag.html', albumName=getAlbumNameFrom(aid), photos=getUsersPhotosByAlbum(aid), base64=base64)

def getUsersPhotosByAlbum(aid):
	cursor = conn.cursor()
	cursor.execute(''' SELECT P.picture_id, P.imgdata, P.caption, U.email
		FROM Pictures AS P, Album AS A, Users AS U
		WHERE P.aid = A.aid AND A.user_id = U.user_id AND A.aid = '{0}' '''.format(aid))
	return cursor.fetchall()

def getAlbumNameFrom(aid):
	cursor = conn.cursor()
	cursor.execute("SELECT aname FROM Album WHERE aid = " + str(aid))
	return cursor.fetchone()[0]

# For friend's functinality:
@app.route('/friend', methods=['GET', 'POST'])
@flask_login.login_required
def friend():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		friendEmail_row = request.form.get('friend')
		friendEmail = friendEmail_row[2:len(friendEmail_row)-3]
		fid = getUserIdFromEmail(friendEmail)

		print("\n uid is: " + str(uid))
		print("fid is: " + str(fid))

		if (uid != fid):
			cursor = conn.cursor()
			cursor.execute('''INSERT INTO friendWith (user1, user2) VALUES (%s, %s)''', (uid, fid))
			cursor.execute('''INSERT INTO friendWith (user1, user2) VALUES (%s, %s)''', (fid, uid))
			conn.commit()
			return gotoHelloPage("Friend made!")
		else:
			return gotoHelloPage("WARNING: CANNOT MAKE FRIEND WITH YOURSELF!")

	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('friend.html', users = getUserList())

def getUsersFriendsID(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT user2 FROM friendWith AS F WHERE F.user1 = '{0}'".format(uid))

	try:
		return cursor.fetchall()[0]
	except:
		return []

def getUsersFriendsEmail(uid):
	friend_id_list = getUsersFriendsID(uid)
	friend_email = []

	for friend_id in friend_id_list:
		friend_email.append(getUseremailFromid(friend_id))

	return friend_email

@app.route("/deleteFriend/<friendEmail>", methods=['GET'])
@flask_login.login_required
def deleteFriend(friendEmail):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	try:
		friend_id = getUserIdFromEmail(friendEmail)
		cursor = conn.cursor()
		cursor.execute('''DELETE FROM friendWith WHERE user1 = '{0}' AND user2 = '{1}' '''.format(uid, friend_id))
		cursor.execute('''DELETE FROM friendWith WHERE user1 = '{0}' AND user2 = '{1}' '''.format(friend_id, uid))
		conn.commit()
		return gotoHelloPage("Friend deleted!") 
	except:
		print("fail to delete friend = " + str(friend_id))
		return gotoHelloPage("Friend deletion unsuccessful") 

#end friend made code

#default page
@app.route("/", methods=['GET'])
def hello():
	try:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('hello.html',
			message='Welecome to Photoshare',
			name=flask_login.current_user.id,
			contributors=getTopContributor(),
			tags=getAllTags(),
			mostPopularTag=getMostPopularTag(),
			allphotos=getAllUsersPhotos(),
			allcomments=getAllComment(),
			base64=base64)
	except:
		return render_template('hello.html',
			message='Welecome to Photoshare',
			contributors=getTopContributor(),
			tags=getAllTags(),
			mostPopularTag=getMostPopularTag(),
			allphotos=getAllUsersPhotos(),
			allcomments=getAllComment(),
			base64=base64)

def gotoHelloPage(message):
	try:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('hello.html',
				name=flask_login.current_user.id,
				message=message,
				contributors=getTopContributor(),
				friends = getUsersFriendsEmail(uid),
				albums=getUsersAlbum(uid),
				userphotos=getUsersPhotos(uid),
				allphotos=getAllUsersPhotos(),
				allcomments=getAllComment(),
				likes=getLikes(),
				tags=getAllTags(),
				mostPopularTag=getMostPopularTag(),
				base64=base64)
	except:
		return render_template('hello.html',
		message='Welecome to Photoshare. Comment Left',
		contributors=getTopContributor(),
		tags=getAllTags(),
		mostPopularTag=getMostPopularTag(),
		allphotos=getAllUsersPhotos(),
		allcomments=getAllComment(),
		base64=base64)

# For comment functinality:
@app.route("/comment/<int:pid>", methods=['POST'])
def comment(pid):
	# Getting the current user id:
	try:
		uid = getUserIdFromEmail(flask_login.current_user.id)
	except:
		uid = 1

	# Get the comment:
	comment = request.form['comment']
	print("Comment left is: " + str(comment))
	print("pid is: " + str(pid))
	print()

	# Getting the date for now:
	now = datetime.now()
	# Format date:
	formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')

	photoOwnerID = getPhotoOwnerID(pid)

	if photoOwnerID != uid:
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO PComment (ctext, cdate, user_id, picture_id) 
				VALUES ('{0}', '{1}', '{2}', '{3}')'''.format(comment, formatted_date, uid, pid))
		conn.commit()

		if uid == 1:
			cursor.execute(''' UPDATE Users
				SET contribution = 0
				WHERE Users.user_id = 1 ''')
			conn.commit()

		return gotoHelloPage("comment left")
	else:
		return gotoHelloPage("You CANNOT leave comment on your own photo")

# get the album id given the album name:
def getPhotoOwnerID(pid):
	cursor = conn.cursor()
	cursor.execute('''SELECT user_id
		FROM Album AS A, Pictures AS P
		WHERE A.aid = P.aid AND P.picture_id = '{0}' '''.format(pid))
	return cursor.fetchone()[0]

def getCommentFor(pid):
	cursor = conn.cursor()
	cursor.execute('''SELECT ctext FROM PComment WHERE picture_id='{0}' '''.format(pid))
	return cursor.fetchall()

def getAllComment():
	cursor = conn.cursor()
	cursor.execute('''SELECT ctext, picture_id, PComment.user_id, cdate, Users.email, PComment.cid
						FROM PComment, Users
						WHERE PComment.user_id = Users.user_id ''')
	return cursor.fetchall()

@app.route("/deleteComment/<cid>", methods=['GET'])
def deleteComment(cid):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM PComment WHERE cid = " + str(cid))
	conn.commit()
	
	return render_template('hello.html',
		message='Comment deleted!',
		contributors=getTopContributor(),
		tags=getAllTags(),
		mostPopularTag=getMostPopularTag(),
		allphotos=getAllUsersPhotos(),
		allcomments=getAllComment(),
		base64=base64)

# End of Comment Functionality

# For like's functinality:
@app.route('/like<uid> <pid>', methods=['POST'])
@flask_login.login_required
def like(uid, pid):
	try:
		cursor = conn.cursor()
		print("Posting Like to the server:")
		print("uid is " + str(uid))
		print("pid is " + str(pid))
		print()
		cursor.execute('''INSERT INTO likes (user_id, picture_id) VALUES (%s, %s)''', (uid, pid))
		conn.commit()
		return gotoHelloPage("Liked!")
	except:
		return gotoHelloPage("You have already liked this photo!")

# For unlike:
@app.route('/unlike<uid> <pid>', methods=['POST'])
@flask_login.login_required
def unlike(uid, pid):
	try:
		cursor = conn.cursor()
		print("Sending 'Deleting the like' to the server:")
		print("uid is " + str(uid))
		print("pid is " + str(pid))
		print()
		cursor.execute('''DELETE FROM likes WHERE user_id = %s AND picture_id = %s''', (uid, pid))
		conn.commit()
		return gotoHelloPage("Unliked!")
	except:
		return gotoHelloPage("You have never liked this photo!")
# End like method here

# For tag's functinality:
@app.route("/tag<int:pid>", methods=['POST'])
@flask_login.login_required
def tag(pid):

	word = request.form.get('word')

	print("picture_id is " + str(pid))
	print("word is: " + str(word))
	
	try:
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO tag (word, picture_id) VALUES (%s, %s)''', (word, pid))
		conn.commit()
		return gotoHelloPage("Tag made!")
	except:
		return gotoHelloPage("You have already tagged this photo with the same tag!")

@app.route("/newTag<int:pid>", methods=['POST'])
@flask_login.login_required
def newTag(pid):
	word = request.form.get('word')

	print("picture_id is " + str(pid))
	print("word is: " + str(word))

	cursor = conn.cursor()
	cursor.execute('''INSERT INTO tag (word, picture_id) VALUES (%s, %s)''', (word, pid))
	conn.commit()
	return gotoHelloPage("Tag made!")

@app.route("/viewPhotoByTag", methods=['POST'])
def viewPhotoByTag():
	word = request.form.get('word')

	return render_template('viewByTag.html', tag=True, word=word, photos=getPhotosByTag(word), base64=base64)

@app.route("/viewYourPhotoByTag", methods=['POST'])
@flask_login.login_required
def viewYourPhotoByTag():

	uid = getUserIdFromEmail(flask_login.current_user.id)
	word = request.form.get('word')

	return render_template('viewByTag.html', tag=True, uid=uid, word=word, photos=getUserPhotosByTag(word, uid), base64=base64)

@app.route("/viewTag/<word>", methods=['GET'])
def viewByTagLink(word):
	return render_template('viewByTag.html', tag=True, word=word, photos=getPhotosByTag(word), base64=base64)

@app.route("/searchPhotoByTag", methods=['POST'])
def searchPhotoByTag():
	userQuery = request.form.get('query')

	query_list = userQuery.split()

	return render_template('viewByTag.html', tag=True, word=userQuery, photos=getPhotosWithAllTagsInQuery(query_list), base64=base64)

def getPhotosWithAllTagsInQuery(qlist):
	if not qlist:
		print("query list is empty")
		return []
	else:
		sql_query = ''' (SELECT picture_id
					FROM tag
					WHERE word = "{0}") '''.format(qlist[0])

		qlist.pop(0)

		for query in qlist:
			outer_Query = ''' SELECT picture_id
							FROM tag
							WHERE word = "{0}" AND picture_id IN  '''.format(query)

			sql_query = "(" + outer_Query + sql_query + ")"

		sql_query = '''SELECT P.picture_id, P.imgdata, P.caption, U.email
			FROM Pictures AS P, Album AS A, Users AS U
			WHERE P.aid = A.aid AND A.user_id = U.user_id AND P.picture_id in ''' + sql_query

		cursor = conn.cursor()
		cursor.execute(sql_query)
		return cursor.fetchall()

def getAllTags():
	cursor = conn.cursor()
	cursor.execute(''' SELECT DISTINCT word FROM tag''')
	return cursor.fetchall()

def getPhotosByTag(word):
	cursor = conn.cursor()
	cursor.execute(''' SELECT P.picture_id, P.imgdata, P.caption, U.email
						FROM tag AS T, Pictures AS P, Album As A, Users As U
						WHERE T.word = '{0}' AND T.picture_id = P.picture_id 
						AND P.aid = A.aid AND A.user_id = U.user_id '''.format(word))
	return cursor.fetchall()

def getUserPhotosByTag(word, uid):
	cursor = conn.cursor()
	cursor.execute(''' SELECT P.picture_id, P.imgdata, P.caption, U.email
						FROM tag AS T, Pictures AS P, Album As A, Users As U
						WHERE T.word = '{0}' AND T.picture_id = P.picture_id 
						AND P.aid = A.aid AND A.user_id = U.user_id
						AND U.user_id = '{1}' '''.format(word, uid))
	return cursor.fetchall()

def getMostPopularTag():
	cursor = conn.cursor()
	cursor.execute(''' SELECT word, COUNT(word)
						FROM tag
						GROUP BY word
						ORDER BY COUNT(word) desc
						limit 1 ''')
	try:
		return cursor.fetchone()[0]
	except:
		return []
#end tag made code

# For Recommendation functionality:
def getTopFiveUsedTagForUser(uid):
	cursor = conn.cursor()
	
	sql_query = ''' SELECT word
			FROM tag AS T, Pictures AS P, Album AS A, Users AS U
			WHERE T.picture_id = P.picture_id AND P.aid = A.aid AND A.user_id = U.user_id AND U.user_id = '{0}'
			GROUP BY word
			ORDER BY COUNT(word) desc
			LIMIT 5 '''.format(uid)

	cursor.execute(sql_query)
	return cursor.fetchall()

def getAllPhotoNotBy(uid):
	cursor = conn.cursor()
	
	cursor.execute(''' SELECT P.picture_id
		FROM Pictures AS P, Album AS A
		WHERE P.aid = A.aid AND A.user_id <> ''' + str(uid))

	return cursor.fetchall()


def rankPhotoID(uid):

	topFiveTag_List = getTopFiveUsedTagForUser(uid)
	
	topFiveTag_String = ""

	for tag in topFiveTag_List:
		topFiveTag_String += "\"" + str(tag[0]) + "\", "
		
	topFiveTag_String = topFiveTag_String[:-2]

	print("Top five tag is: " + topFiveTag_String)

	allOtherUsersPhotosID_sql = getAllPhotoNotBy(uid)

	allOtherUsersPhotosID = []

	for pid in allOtherUsersPhotosID_sql:
		allOtherUsersPhotosID.append(pid[0])

	print("allOtherUsersPhotosID:")
	print(allOtherUsersPhotosID)

	cursor = conn.cursor()

	recommendandedPhoto_list = []

	for photoID in allOtherUsersPhotosID:
		print()

		# getting the numberOfTagSatisfied among the top five for this photo
		print("current photoID is: " + str(photoID))

		cursor.execute(''' SELECT COUNT(*)
			FROM tag
			WHERE picture_id = '{0}' AND word IN ({1}) '''.format(photoID, topFiveTag_String))
		
		numberOfTagSatisfied = cursor.fetchone()[0]

		print("numberOfTagSatisfiedAmongTopFive is: " + str(numberOfTagSatisfied))

		# if this photo satisfied none of it, skip it
		if numberOfTagSatisfied != 0:

			# Getting the numberOfTag this photo has
			cursor.execute("SELECT COUNT(word) FROM tag WHERE picture_id = " + str(photoID))

			numberOfTag = cursor.fetchone()[0]

			recommendandedPhoto_list.append((photoID, numberOfTagSatisfied, numberOfTag))

	print("recommendandedPhoto_list:")
	print(recommendandedPhoto_list)

	def sort_key(e):
		return (-e[1], e[2])

	recommendandedPhoto_list.sort(key=sort_key)

	return [e[0] for e in recommendandedPhoto_list]

@app.route("/recommendation", methods=["GET"])
@flask_login.login_required
def recommendation():

	uid = getUserIdFromEmail(flask_login.current_user.id)

	recommendedPhotoID_list = rankPhotoID(uid)

	print("recommendedPhotoID_list:")
	print(recommendedPhotoID_list)

	recommendedPhotoData = getPhotosBy(recommendedPhotoID_list)

	return render_template('recommendation.html', photos=recommendedPhotoData, base64=base64)


def getPhotoBy(pid):
	cursor = conn.cursor()
	
	cursor.execute(''' SELECT P.picture_id
		FROM Pictures AS P, Album AS A
		WHERE P.aid = A.aid AND A.user_id <> ''' + str(uid))

	return cursor.fetchall()

def getPhotosBy(pid_list):

	cursor = conn.cursor()

	imgdata_list = []

	for pid in pid_list:
		cursor.execute(''' SELECT P.imgdata, P.caption, U.email
			FROM Pictures AS P, Album AS A, Users AS U
			WHERE P.aid = A.aid AND A.user_id = U.user_id AND P.picture_id = '{0}' '''.format(pid))
		imgdata_list.append(cursor.fetchone())

	return imgdata_list


#end Recommendation made code

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)