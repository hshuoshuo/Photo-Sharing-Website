CREATE TABLE WUser (
	uid    INT PRIMARY KEY,
    first_name  CHAR(10),
    last_name  CHAR(10),
    email   CHAR(20) NOT NULL,
    Date_of_Birth    DATE,
    hometown  CHAR(10),
    gender   CHAR(6),  
    pass_word    CHAR(20) NOT NULL,
    CONSTRAINT sameEmail UNIQUE (email),
    CONSTRAINT sameUid UNIQUE (uid));

CREATE TABLE Album (aid INT,
			aname   CHAR(10),
			uid    INT REFERENCES WUser on DELETE CASCADE,
			date_of_creation DATE);

CREATE TABLE Photo (pid INTEGER,
					caption VARCHAR(20),
                    p_data BINARY,
                    aid INTEGER,
                    PRIMARY KEY(pid),
					FOREIGN KEY(aid) REFERENCES Album);
                    
CREATE TABLE PComment (cid    INT PRIMARY KEY,
						ctext    CHAR(200),
						cdate    DATE,
						uid    INT REFERENCES WUser,
						pid    INT REFERENCES Photo);


CREATE TABLE Tag (word VARCHAR(20),    
				 pid INTEGER,
                 PRIMARY KEY(word),
                 FOREIGN KEY(pid) REFERENCES Photo);
                    
				
CREATE TABLE Friend (uid    INT REFERENCES WUser,
					fid     INT,  
                    PRIMARY KEY(uid));
                    
CREATE ASSERTION noCommentOnSelfPhoto CHECK (
	EXISTS (
		SELECT C.uid
		FROM PComment AS C
        	NOT IN(SELECT W.uid
					FROM Photo AS P, Album AS A, WUser AS W
					WHERE P.aid = A.aid, A.uid = W.uid, P.pid = C.pid));

DELIMITER $$
CREATE TRIGGER after_photo AFTER INSERT ON Comment 
    FOR EACH ROW
    BEGIN
        UPDATE WUser
		SET contribution = contribution + 1
		WHERE WUser.uid = NEW.uid;
	END; $$
DELIMITER ;
