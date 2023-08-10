CREATE DATABASE  IF NOT EXISTS `improbability_sms_assistant` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `improbability_sms_assistant`;
-- MySQL dump 10.13  Distrib 8.0.27, for Win64 (x86_64)
--
-- Host: localhost    Database: improbability_sms_assistant
-- ------------------------------------------------------
-- Server version	8.0.32-24

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `assistants`
--

DROP TABLE IF EXISTS `assistants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assistants` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT 'The User ID of the User associated with the Assistant.',
  `name` varchar(24) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'The name of the Assistant.',
  `disposition` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'A short description of the disposition of the Assistant. ',
  `personality` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'A longer description of the Assistants personality. Can be multiple sentences.',
  `favorite_author` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'The Assistants favorite author. ',
  `origin` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'The location where the Assistant originated. ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp from when the Assistant was created. ',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Timestamp from when the Assistant record was last updated. ',
  PRIMARY KEY (`id`,`user_id`),
  KEY `assistants_ibfk_1` (`user_id`),
  CONSTRAINT `assistants_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_history`
--

DROP TABLE IF EXISTS `user_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `from_field` enum('user','assistant') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `history` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `user_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1078 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `first_name` varchar(24) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'The Users first name.',
  `last_name` varchar(24) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'The Users last name.',
  `title` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Consultant' COMMENT 'The Users title.',
  `phone_number` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'The Users email address.',
  `description` text COLLATE utf8mb4_unicode_ci,
  `expectations` text COLLATE utf8mb4_unicode_ci,
  `country` varchar(4) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ca',
  `location` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT 'Vancouver, Canada',
  `languages` varchar(4) COLLATE utf8mb4_unicode_ci DEFAULT 'en' COMMENT 'A comma seperated list of spoken languages of the user.',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`,`phone_number`),
  UNIQUE KEY `phone_number` (`phone_number`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-08-10 12:48:56
