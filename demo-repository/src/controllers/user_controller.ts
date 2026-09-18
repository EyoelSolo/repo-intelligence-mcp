import { UserService } from "../services/user_service";

export class UserController {
    constructor(
        private userService: UserService
    ) {}

    async getUser(id: string) {
        return this.userService.getUser(id);
    }
}