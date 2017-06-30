CREATE TABLE binpackages (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	udeb INTEGER,
	control TEXT,
	Version TEXT,
	Architecture TEXT,
	Size INTEGER,
	MD5Sum TEXT,
	SHA1 TEXT,
	SHA256 TEXT,
	Description_md5 TEXT
);
CREATE INDEX bpname ON binpackages (name, Architecture);

CREATE TABLE srcpackages (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	dsc TEXT,
	Directory TEXT,
	Priority TEXT,
	Section TEXT
);

CREATE TABLE releases (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	Codename TEXT
);
CREATE UNIQUE INDEX relcodename ON releases (Codename);

CREATE TABLE release_bin (
	idrel INTEGER,
	idpkg INTEGER,
	component TEXT,
	Filename TEXT,
	PRIMARY KEY (idrel, idpkg)
);
CREATE INDEX rbpr ON release_bin (idpkg, idrel);

CREATE TABLE release_src (
	idrel INTEGER,
	idsrc INTEGER,
	component TEXT,
	Directory TEXT,
	PRIMARY KEY (idrel, idsrc)
);

CREATE TABLE dbschema (
	version INTEGER
);

INSERT INTO dbschema VALUES (1);
