import { UserRepository } from "../repositories/user_repository";

export class UserService {

    constructor(
        private repository: UserRepository
    ) {}

    async getUser(id: string) {
        return this.repository.findById(id);
    }

    async deleteUser(id: string) {
        return this.repository.delete(id);
    }
}