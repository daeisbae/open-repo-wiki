import dbConn from '@/db/utils/connector'

export interface FileData {
    file_id: number
    name: string
    language: string | null
    folder_id: number
    content: string
    ai_summary: string | null
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
        content: string
    ): Promise<FileData> {
        const query = `
      INSERT INTO File (name, folder_id, content)
      VALUES ($1, $2, $3)
      ON CONFLICT DO NOTHING
      RETURNING *;
    `
        const values = [name, folderId, content]
        const result = await dbConn.query<FileData>(query, values)

        if (result.rowCount === 0) {
            const getFileQuery =
                'SELECT * FROM File WHERE name = $1 AND folder_id = $2'
            const getFileValues = [name, folderId]
            const getFileResult = await dbConn.query(getFileQuery, getFileValues)
            return getFileResult.rows[0]
        }

        return result.rows[0]
    }

    async update(ai_summary: string, file_id: number): Promise<FileData> {
        const query = `
      UPDATE File 
      SET ai_summary = $1
      WHERE file_id = $2
      RETURNING *;
    `
        const values = [ai_summary, file_id]
        const result = await dbConn.query<FileData>(query, values)
        return result.rows[0]
    }
}
