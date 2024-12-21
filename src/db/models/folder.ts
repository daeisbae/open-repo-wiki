import dbConn from '@/db/utils/connector'

export interface FolderData {
    folder_id: number
    name: string
    path: string
    parent_folder_id: number
    ai_summary: string | null
    branch_id: number
}

export class Folder {
    async select(branch_id: number): Promise<Array<FolderData> | null> {
        const query = 'SELECT * FROM Folder WHERE branch_id = $1'
        return (await dbConn.query(query, [branch_id])).rows || null
    }

    async insert(
        name: string,
        path: string,
        branch_id: number,
        parent_folder_id: number | null
    ): Promise<FolderData> {
        const query =
            parent_folder_id === null
                ? `
            INSERT INTO Folder (name, path, branch_id)
            VALUES ($1, $2, $3)
            RETURNING *;
        `
                : `
            INSERT INTO Folder (name, path, branch_id, parent_folder_id)
            VALUES ($1, $2, $3, $4)
            RETURNING *;
        `
        const values =
            parent_folder_id === null
                ? [name, path, branch_id]
                : [name, path, branch_id, parent_folder_id]
        const result = await dbConn.query(query, values)
        return result.rows[0]
    }

    async update(ai_summary: string, folder_id: number): Promise<FolderData> {
        const query = `
            UPDATE Folder 
            SET ai_summary = $1
            WHERE folder_id = $2
            RETURNING *;
        `

        const values = [ai_summary, folder_id]
        const result = await dbConn.query(query, values)
        return result.rows[0]
    }
}
