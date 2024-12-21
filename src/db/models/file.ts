import dbConn from '@/db/utils/connector'

export interface FileData {
    file_id: number
    name: string
    language: string
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
        language: string,
        folderId: number,
        content: string
    ): Promise<FileData> {
        const query = `
      INSERT INTO File (name, language, folder_id, content)
      VALUES ($1, $2, $3, $4)
      RETURNING *;
    `
        const values = [name, language, folderId, content]
        const result = await dbConn.query<FileData>(query, values)
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
