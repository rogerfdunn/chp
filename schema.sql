CREATE TABLE `TBL_Incidents` (
	`id` INT(11) NOT NULL AUTO_INCREMENT,
	`startime` DATETIME NOT NULL,
	`endtime` DATETIME NOT NULL,
	`type` VARCHAR(50) NOT NULL,
	`dispatchcenter` VARCHAR(10) NOT NULL,
	`location` VARCHAR(160) NULL DEFAULT NULL,
	`CHPIncidentID` VARCHAR(20) NOT NULL,
	`DetailText` TEXT NULL,
	`area` VARCHAR(30) NULL DEFAULT NULL,
	`currentTemp` INT(11) NULL DEFAULT NULL,
	`currentWeather` VARCHAR(40) NULL DEFAULT NULL,
	PRIMARY KEY (`id`)
);