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
    FOREIGN KEY (mail) REFERENCES user(mail)
);

CREATE TABLE sensor (
    id INT PRIMARY KEY AUTO_INCREMENT,
    estado BOOLEAN NOT NULL,
    roto BOOLEAN DEFAULT FALSE,
    version DECIMAL(10, 2) NOT NULL,
    ultimo_repuesto DATETIME NOT NULL
);

CREATE TABLE sensor_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sensor_id INT NOT NULL,
    lectura DECIMAL(10, 2) NOT NULL,
    log_fecha DATETIME NOT NULL,
    FOREIGN KEY (sensor_id) REFERENCES sensor(id)
)