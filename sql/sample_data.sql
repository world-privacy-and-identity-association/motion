-- sample data for scheme version 4
INSERT INTO voter (id,email) VALUES (1, 'User A');
INSERT INTO voter (id,email) VALUES (2, 'User B');
INSERT INTO voter (id,email) VALUES (3, 'User C');
ALTER SEQUENCE voter_id_seq RESTART WITH 4;

INSERT INTO motion (id,identifier,name,type,host,content,posed,posed_by,deadline,canceled,cancelation_reason,canceled_by) VALUES
    (1,'g1.20200402.001','Motion A','group1','127.0.0.1:5000','My special motion','2020-04-02 21:40:33.780364',1,'2020-04-02 21:40:33.780364',Null,Null,Null);
INSERT INTO motion (id,identifier,name,type,host,content,posed,posed_by,deadline,canceled,cancelation_reason,canceled_by) VALUES
    (2,'g1.20200402.002','Motion B','group1','127.0.0.1:5000','A second motion','2020-04-02 21:41:26.588442',1,'2020-04-04 21:41:26.588442',Null,Null,Null);
INSERT INTO motion (id,identifier,name,type,host,content,posed,posed_by,deadline,canceled,cancelation_reason,canceled_by) VALUES
    (3,'g1.20200402.003','Motion C','group1','127.0.0.1:5000','A third motion', '2020-04-02 21:47:24.969588',1,'2020-04-04 21:47:24.969588','2020-04-03 21:48:24.969588','Entered with wrong text',1);
-- add motion with timespan from now to 1 day from now
INSERT INTO motion (id,identifier,name,type,host,content,posed,posed_by,deadline,canceled,cancelation_reason,canceled_by) VALUES
    (4,'g1.20200402.004','Motion D','group1','127.0.0.1:5000','A fourth motion', current_timestamp ,1,current_timestamp + interval '1' day,Null,Null,Null);
ALTER SEQUENCE motion_id_seq RESTART WITH 5;

INSERT INTO vote (motion_id,voter_id,result,entered) VALUES (1,1,'yes','2020-04-02 21:54:34.469784');
INSERT INTO vote (motion_id,voter_id,result,entered) VALUES (1,2,'yes','2020-04-02 21:54:34.469784');
INSERT INTO vote (motion_id,voter_id,result,entered) VALUES (1,3,'no','2020-04-02 21:54:34.469784');
INSERT INTO vote (motion_id,voter_id,result,entered) VALUES (2,1,'yes','2020-04-02 21:54:34.469784');
INSERT INTO vote (motion_id,voter_id,result,entered) VALUES (2,2,'no','2020-04-02 21:54:34.469784');
INSERT INTO vote (motion_id,voter_id,result,entered) VALUES (2,3,'no','2020-04-02 21:54:34.469784');
INSERT INTO vote (motion_id,voter_id,result,entered) VALUES (3,3,'yes','2020-04-02 21:48:34.469784');
