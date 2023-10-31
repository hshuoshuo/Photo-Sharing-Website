CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;
DROP TABLE IF EXISTS Pictures CASCADE;
DROP TABLE IF EXISTS Users CASCADE;
DROP TABLE IF EXISTS Album CASCADE;

CREATE TABLE Users (
	user_id			int4 PRIMARY KEY AUTO_INCREMENT,
    first_name		varchar(255),
    last_name		varchar(255),
    email			varchar(255) NOT NULL,
    DOB				DATE,
    hometown		CHAR(10),
    gender			CHAR(10),  
    password 		varchar(255),
    contribution	INT DEFAULT 0,
    CONSTRAINT sameEmail UNIQUE (email)
);

CREATE TABLE friendWith (
	user1			INT REFERENCES Users(user_id),
    user2			INT REFERENCES Users(user_id),
    PRIMARY KEY (user1, user2)
);

CREATE TABLE Album (
	aid				int4 PRIMARY KEY AUTO_INCREMENT,
    aname			VARCHAR(50),
    user_id			int4 REFERENCES Users on DELETE CASCADE,
    CONSTRAINT noDuplicateAlbum UNIQUE (user_id, aname),
    date_of_creation DATE
);

CREATE TABLE Pictures (
	picture_id 		int4  AUTO_INCREMENT,
	caption 		VARCHAR(255),
	imgdata 		longblob,
	aid 			int4,
    FOREIGN KEY (aid) REFERENCES Album (aid) ON DELETE CASCADE,
	PRIMARY KEY(picture_id)
);

CREATE TABLE PComment (
	cid				int4 PRIMARY KEY AUTO_INCREMENT,
    ctext			CHAR(200),
    cdate			DATE,
    user_id			int4,
    picture_id		int4,
    FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE,
	FOREIGN KEY (picture_id) REFERENCES Pictures (picture_id) ON DELETE CASCADE
);

CREATE TABLE tag (
	word 			VARCHAR(20),  
    picture_id		int4,
	PRIMARY KEY (word, picture_id),
    FOREIGN KEY (picture_id) REFERENCES Pictures (picture_id) ON DELETE CASCADE
);

CREATE TABLE likes (
	user_id			INT REFERENCES Users,
    picture_id		int4 REFERENCES Pictures ON DELETE CASCADE,
    PRIMARY KEY(user_id, picture_id)
);

CREATE TRIGGER after_photo AFTER INSERT ON Pictures 
	FOR EACH ROW
        UPDATE Users
		SET contribution = contribution + 1
		WHERE Users.user_id = (SELECT * FROM (SELECT U.user_id
			FROM Users AS U, Album AS A, Pictures AS P
			WHERE P.picture_id = NEW.picture_id AND P.aid = A.aid AND A.user_id = U.user_id) AS X);

CREATE TRIGGER after_comment AFTER INSERT ON PComment 
    FOR EACH ROW
        UPDATE Users
		SET contribution = contribution + 1
		WHERE Users.user_id = New.user_id;
        
CREATE TRIGGER after_comment_d BEFORE DELETE ON PComment 
    FOR EACH ROW
        UPDATE Users
		SET contribution = contribution - 1
		WHERE Users.user_id = OLD.user_id;

CREATE TRIGGER after_photo_d BEFORE DELETE ON Pictures 
	FOR EACH ROW
        UPDATE Users
		SET contribution = contribution - 1
		WHERE Users.user_id = (SELECT * FROM (SELECT U.user_id
			FROM Users AS U, Album AS A, Pictures AS P
			WHERE P.picture_id = OLD.picture_id AND P.aid = A.aid AND A.user_id = U.user_id) AS X);
            
CREATE TRIGGER after_album_d BEFORE DELETE ON Album 
	FOR EACH ROW
        UPDATE Users
		SET contribution = contribution - (SELECT COUNT(*)
				FROM Pictures AS P
				WHERE P.aid = OLD.aid)
		WHERE Users.user_id = (SELECT * FROM (SELECT U.user_id
			FROM Users AS U, Album AS A
			WHERE OLD.aid = A.aid AND A.user_id = U.user_id) AS X);

INSERT INTO Users (user_id, email) VALUES (1, 'Guest user');
INSERT INTO Users (email, password) VALUES ('test@bu.edu', 'test');
INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');
