import dbConn from '@/db/utils/connector'

export interface FolderData {
    folder_id: number
    name: string
    path: string
    parent_folder_id: number | null
    ai_summary: string | null
    branch_id: number
    usage: string | null
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
            ON CONFLICT DO NOTHING
            RETURNING *;
        `
                : `
            INSERT INTO Folder (name, path, branch_id, parent_folder_id)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT DO NOTHING
            RETURNING *;
        `
        const values =
            parent_folder_id === null
                ? [name, path, branch_id]
                : [name, path, branch_id, parent_folder_id]
        const result = await dbConn.query(query, values)

        if (result.rowCount === 0) {
            const getFolderQuery =
                parent_folder_id === null
                    ? 'SELECT * FROM Folder WHERE path = $1 AND branch_id = $2'
                    : 'SELECT * FROM Folder WHERE path = $1 AND branch_id = $2 AND parent_folder_id = $3'
            const getFolderValues =
                parent_folder_id === null
                    ? [name, path, branch_id]
                    : [name, path, branch_id, parent_folder_id]
            const getFolderResult = await dbConn.query(getFolderQuery, getFolderValues)
            return getFolderResult.rows[0]
        }

        return result.rows[0]
    }

    async update(ai_summary: string, usage: string, folder_id: number): Promise<FolderData> {
        const query = `
            UPDATE Folder 
            SET ai_summary = $1, usage = $2
            WHERE folder_id = $3
            RETURNING *;
        `

        const values = [ai_summary, usage, folder_id]
        const result = await dbConn.query(query, values)
        return result.rows[0]
    }

    async delete(folder_id: number): Promise<void> {
        const query = 'DELETE FROM Folder WHERE folder_id = $1'
        await dbConn.query(query, [folder_id])
    }
}
