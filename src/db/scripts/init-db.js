import { createRequire } from "module";
const require = createRequire(import.meta.url);
const { Client } = require("pg");
const { readFile } = require("fs/promises");
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { DBConfig } from "../config/config.js";
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";

const __dirname = dirname(fileURLToPath(import.meta.url));

async function downloadCertificate() {
	const s3Client = new S3Client({
		region: DBConfig.certificateRegion,
		endpoint: DBConfig.certificateLink,
		credentials: {
			accessKeyId: DBConfig.certificateAccessKeyID,
			secretAccessKey: DBConfig.certificateSecretAccessKey,
		},
	});

	try {
		const command = new GetObjectCommand({
			Bucket: DBConfig.certificateBucket,
			Key: DBConfig.certificateFile,
		});

		const response = await s3Client.send(command);
		const certificateData = await response.Body.transformToString();
		return certificateData;
	} catch (error) {
		console.error("Failed to download certificate:", error);
		throw error;
	}
}

async function initDatabase() {
	console.log("Initializing database with config:", {
		host: DBConfig.host,
		port: DBConfig.port,
		database: DBConfig.database,
		user: DBConfig.user,
		password: DBConfig.password,
		certificateLink: DBConfig.certificateLink,
	});

	const { config, certificateLink } = DBConfig;

	let pgClient = undefined;

	if (!certificateLink) {
		pgClient = new Client({
			...config,
		});
	} else {
		const certificateData = await downloadCertificate();
		pgClient = new Client({
			...config,
			ssl: {
				rejectUnauthorized: false,
				ca: certificateData,
				sslmode: "require",
			},
		});
	}

	await pgClient.connect();

	await pgClient
		.query(`CREATE DATABASE ${DBConfig.database};`)
		.catch((error) => {
			console.log("❌ Database is already created");
		})
		.then(() => {
			console.log("✅ Database created successfully");
		});

	const schemaPath = join(__dirname, "../migrations/create_tables.sql");
	const sql = await readFile(schemaPath, "utf8");

	await pgClient.query(sql).catch((error) => {
		console.error("❌ Schema loading failed:", error);
	});
	console.log("✅ Schema loaded successfully");
	pgClient.end();
}

initDatabase()
	.then(() => {
		console.log("✅ Database initialization complete");
		process.exit(0);
	})
	.catch((error) => {
		console.error("❌ Fatal error:", error);
		process.exit(1);
	});
