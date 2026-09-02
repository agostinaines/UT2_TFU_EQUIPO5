DROP DATABASE IF EXISTS tfu2;
CREATE DATABASE tfu2;
USE tfu2;

CREATE TABLE usuario (
	mail VARCHAR(320) PRIMARY KEY,
	nombre VARCHAR(32) NOT NULL CHECK ( CHAR_LENGTH(nombre) >= 3 ),
    apellido VARCHAR(32) NOT NULL CHECK ( CHAR_LENGTH(apellido) >= 3 ),
    rol ENUM('operador') DEFAULT 'operador' NOT NULL
);

CREATE TABLE login (
    mail VARCHAR(50) PRIMARY KEY,
    contrasenia VARCHAR(200) NOT NULL,
    FOREIGN KEY (mail) REFERENCES usuario(mail)
);

CREATE TABLE sensor (
    id INT PRIMARY KEY AUTO_INCREMENT,
    activo BOOLEAN NOT NULL DEFAULT FALSE,
    roto BOOLEAN DEFAULT FALSE,
    version DECIMAL(10, 2) NOT NULL,
    ultimo_repuesto DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE sensor_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sensor_id INT NOT NULL,
    lectura DECIMAL(10, 2) NOT NULL,
    log_fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES sensor(id)
);

INSERT INTO sensor (activo, roto, version) VALUES
(1.11),
(1.11),
(1.11),
(1.11),
(1.12),
(1.12);

SELECT * FROM sensor_logs;

CREATE USER 'unknown_user'@'%' IDENTIFIED BY 'Unknown19976543!';
CREATE USER 'usuario_user'@'%' IDENTIFIED BY 'Usuario19976543!';

# GRANTS UNKNOWN
GRANT INSERT, SELECT ON tfu2.login TO 'unknown_user'@'%';
GRANT INSERT, SELECT ON tfu2.usuario TO 'unknown_user'@'%';

# GRANTS USUARIO
GRANT SELECT, UPDATE, INSERT ON tfu2.sensor TO 'usuario_user'@'%';
GRANT SELECT, UPDATE, INSERT ON tfu2.sensor_logs TO 'usuario_user'@'%';
