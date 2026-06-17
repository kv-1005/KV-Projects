import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { simulator } from '../simulation/S71200Simulator';

export type UserRole = 'OPERATOR' | 'ENGINEER' | 'ADMIN';

interface User {
    id: string;
    username: string;
    name: string;
    role: UserRole;
}

const DEMO_USERS: Record<string, { password: string; user: User }> = {
    operator: {
        password: 'op123',
        user: { id: '1', username: 'operator', name: 'A. Kumar', role: 'OPERATOR' },
    },
    engineer: {
        password: 'eng456',
        user: { id: '2', username: 'engineer', name: 'R. Sharma', role: 'ENGINEER' },
    },
    admin: {
        password: 'admin789',
        user: { id: '3', username: 'admin', name: 'System Admin', role: 'ADMIN' },
    },
};

interface AuthState {
    user: User | null;
    loginError: string | null;
    sessionStart: Date | null;
    login: (username: string, password: string) => boolean;
    logout: () => void;
    hasPermission: (minRole: UserRole) => boolean;
}

const roleLevel: Record<UserRole, number> = { OPERATOR: 1, ENGINEER: 2, ADMIN: 3 };

export const useAuthStore = create<AuthState>()(
    persist(
        (set, get) => ({
            user: null,
            loginError: null,
            sessionStart: null,

            login: (username, password) => {
                const entry = DEMO_USERS[username.toLowerCase()];
                if (entry && entry.password === password) {
                    simulator.setUser(entry.user.name);
                    set({ user: entry.user, loginError: null, sessionStart: new Date() });
                    return true;
                }
                set({ loginError: 'Invalid credentials. Check username / password.' });
                return false;
            },

            logout: () => {
                set({ user: null, loginError: null, sessionStart: null });
            },

            hasPermission: (minRole) => {
                const { user } = get();
                if (!user) return false;
                return roleLevel[user.role] >= roleLevel[minRole];
            },
        }),
        { name: 'auth-store', partialize: (s) => ({ user: s.user, sessionStart: s.sessionStart }) }
    )
);
