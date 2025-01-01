import dotenv from "dotenv";
dotenv.config();

export const DBConfig = {
	host: process.env.DB_HOST,
	port: parseInt(process.env.DB_PORT),
	database: process.env.DB_NAME,
	user: process.env.DB_USER,
	password: process.env.DB_PASSWORD,
	certificateLink: process.env.DB_CERTIFICATE_LINK,
	certificateRegion: process.env.DB_CERTIFICATE_REGION,
	certificateBucket: process.env.DB_CERTIFICATE_BUCKET_NAME,
	certificateFile: process.env.DB_CERTIFICATE_FILE,
	certificateAccessKeyID: process.env.DB_CERTIFICATE_ACCESS_KEY_ID,
	certificateSecretAccessKey: process.env.DB_CERTIFICATE_SECRET_ACCESS_KEY,
};
