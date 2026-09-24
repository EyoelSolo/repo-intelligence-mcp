import { UserService } from "../services/user_service";

export class UserRepository {

    async findById(id: string) {
        return {
            id,
            name: "Example User"
        };
    }

    async delete(id: string) {
        return true;
    }
}