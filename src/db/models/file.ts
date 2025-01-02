import dbConn from '@/db/utils/connector'

export interface FileData {
    file_id: number
    name: string
    language: string | null
    folder_id: number
    content: string
    ai_summary: string | null
    usage: string | null
}

export class File {
    async select(folderId: number): Promise<FileData[]> {
        const query = 'SELECT * FROM File WHERE folder_id = $1'
        const result = await dbConn.query<FileData>(query, [folderId])
        return result.rows
    }

    async insert(
        name: string,
        folderId: number,
        content: string,
        ai_summary: string,
        usage: string
    ): Promise<FileData> {
        const query = `
      INSERT INTO File (name, folder_id, content, ai_summary, usage)
      VALUES ($1, $2, $3, $4, $5)
      ON CONFLICT DO NOTHING
      RETURNING *;
    `
        const values = [name, folderId, content, ai_summary, usage]
        const result = await dbConn.query<FileData>(query, values)

        return result.rows[0]
    }
}
