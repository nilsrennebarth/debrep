--
-- Hold binary packages metadata. Each package file in the repository will get
-- exactly one id. If the same package is present in several releases, it will
-- still have only one id, but several references (see below)
--
CREATE TABLE binpackages (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	udeb INTEGER,         -- 1 if the package is a udeb, 0 otherwise
	control TEXT,         -- Content of the binary package control file
	Version TEXT,
	Architecture TEXT,
	Size INTEGER,         -- Size of package file in bytes
	MD5Sum TEXT,
	SHA1 TEXT,
	SHA256 TEXT,
	Description_md5 TEXT
);
CREATE INDEX bpname ON binpackages (name, Architecture);

CREATE TABLE srcpackages (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	dsc TEXT,             -- Content of the dsc File
	Priority TEXT,
	Section TEXT
);

CREATE TABLE releases (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	Codename TEXT
);
CREATE UNIQUE INDEX relcodename ON releases (Codename);

--
-- Hold the binary packages of releases
-- Each release contains a certain number of pacakges, and
-- for each package there is a release specific component and file
-- name (relative to the repository root). The file name of a package
-- with a given id may or may differ between releases. For a package
-- pool it will always be the same but we want to support various
-- repository layouts.
--
CREATE TABLE release_bin (
	idrel INTEGER,        -- id of release (=> releases.id)
	idpkg INTEGER,        -- id of package (=> binpackages.id)
	component TEXT,
	Filename TEXT,        -- Package filename relative to repository root
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
