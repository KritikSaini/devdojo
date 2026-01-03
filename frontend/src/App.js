import React, { useState, useEffect, useCallback } from 'react';
import * as Yup from 'yup';
import { ToastContainer, toast } from "react-toastify";
import 'react-toastify/dist/ReactToastify.css';

// This should be in a separate api.js file, but for a single-file hackathon, it's here.
const API_BASE_URL = 'http://127.0.0.1:8000';

const api = {
    async request(endpoint, { body, ...customConfig } = {}) {
        const token = localStorage.getItem('dojo_token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) {
            headers.Authorization = `Bearer ${token}`;
        }
        const config = {
            method: body ? (customConfig.method || 'POST') : 'GET',
            ...customConfig,
            headers: { ...headers, ...customConfig.headers },
        };
        if (body) {
            config.body = JSON.stringify(body);
        }
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'An API error occurred');
        }
        return response.status === 204 ? {} : response.json();
    },
    login: (username, password) => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        return fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData,
        }).then(async res => {
            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.detail || "Login failed");
            }
            return res.json();
        });
    },
    register: (username, email, password, github_username) => api.request('/auth/register', { body: { username, email, password, github_username } }),
    getMe: () => api.request('/auth/me'),
    updateMe: (github_username) => api.request('/auth/me', { method: 'PUT', body: { github_username } }),
    getGroups: () => api.request('/groups/'),
    getGroup: (groupId) => api.request(`/groups/${groupId}`),
    createGroup: (name, description) => api.request('/groups/', { body: { name, description } }),
    joinGroup: (groupId) => api.request(`/groups/${groupId}/join`, { method: 'POST', body: {} }),
    getGroupLeaderboard: (groupId) => api.request(`/leaderboard/group/${groupId}`),
    createChallenge: (Topic, difficulty, group_id) => api.request('/challenges/', { body: { Topic, difficulty, group_id } }),
    getChallengeHistory: (groupId) => api.request(`/challenges/group/${groupId}`),
    getMySubmissions: () => api.request('/submissions/'),
    forgotPassword: (email) =>
        api.request("/auth/forgot-password", {
            body: { email },
        }),

    resetPassword: (token, new_password) =>
        api.request("/auth/reset-password", {
            body: { token, new_password },
        }),

};


// --- ICONS (using inline SVGs for simplicity) ---
const UsersIcon = ({ className }) => (<svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>);
// eslint-disable-next-line no-unused-vars
const CodeIcon = ({ className }) => (<svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" /></svg>);
const PlusIcon = ({ className }) => (<svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>);
const ArrowLeftIcon = ({ className }) => (<svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" /></svg>);
const LoaderIcon = ({ className }) => (<svg className={className + " animate-spin"} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="currentColor"><defs><linearGradient id="a"><stop offset="0" stopColor="#fff" stopOpacity="0"></stop><stop offset="1" stopColor="#fff"></stop></linearGradient></defs><path stroke="url(#a)" strokeLinecap="round" strokeWidth="15" d="M100 25A75 75 0 0 1 100 175" style={{ transformOrigin: 'center' }}></path></svg>);
const LogOutIcon = ({ className }) => (<svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>);
const UserIcon = ({ className }) => (<svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>);
const XIcon = ({ className }) => (<svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>);
const InfoIcon = ({ className }) => (<svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>);

// --- Shared components ---
const Input = ({ id, type, placeholder, value, onChange, error, disabled }) => (
    <div>
        <label htmlFor={id} className="block text-sm font-medium text-gray-300 mb-1">{placeholder}</label>
        <input id={id} name={id} type={type} value={value} onChange={onChange} disabled={disabled} required={!disabled}
            className={`w-full px-4 py-3 rounded-lg bg-gray-800 border ${error ? 'border-red-500' : 'border-gray-700'} text-white placeholder-gray-500 focus:outline-none focus:ring-2 ${error ? 'focus:ring-red-500' : 'focus:ring-indigo-500'}`}
            placeholder={placeholder} />
        {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
    </div>
);
const Button = ({ children, onClick, type = "button", fullWidth = false, disabled = false, isLoading = false, variant = "primary" }) => {
    const baseClasses = "inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors";
    const variantClasses = {
        primary: "text-white bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500 focus:ring-offset-gray-900",
        secondary: "text-gray-300 bg-gray-700 hover:bg-gray-600 focus:ring-gray-500 focus:ring-offset-gray-800"
    };
    const disabledClasses = "opacity-50 cursor-not-allowed";
    return (<button type={type} onClick={onClick} disabled={disabled || isLoading} className={`${baseClasses} ${variantClasses[variant]} ${fullWidth ? 'w-full' : ''} ${disabled || isLoading ? disabledClasses : ''}`}>{isLoading ? <LoaderIcon className="w-6 h-6" /> : children}</button>);
};
const LoadingSpinner = () => (<div className="flex justify-center items-center p-8"><LoaderIcon className="w-12 h-12 text-indigo-500" /></div>);
const ErrorMessage = ({ message, onRetry }) => (<div className="bg-red-500/20 text-red-400 p-4 rounded-lg text-center"><p>Oops! Something went wrong</p><p className="text-sm my-2">{message}</p>{onRetry && <button onClick={onRetry} className="text-indigo-400 hover:underline">Try again</button>}</div>);

// --- Validation Schemas ---
const loginSchema = Yup.object({ email: Yup.string().email("Invalid email").required("Required"), password: Yup.string().min(4, "Minimum 4 characters").required("Required") });
const registerSchema = Yup.object({ username: Yup.string().min(3, "Minimum 3 letters").required("Required"), email: Yup.string().email("Invalid email").required("Required"), password: Yup.string().min(4, "Minimum 4 characters").required("Required"), github_username: Yup.string().required("GitHub username is required") });
const profileSchema = Yup.object({ github_username: Yup.string().required("Required") });
const createGroupSchema = Yup.object({ name: Yup.string().min(2, "Too short").required("Required"), description: Yup.string().min(2, "Too short").required("Required") });
const createChallengeSchema = Yup.object({ Topic: Yup.string().min(3, "Too short").required("Required"), difficulty: Yup.string().oneOf(['Easy', 'Medium', 'Hard']).required("Required") });

// --- Pages & Components ---
function LoginPage({ navigateTo, onLoginSuccess }) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState(null);
    const [fieldErrors, setFieldErrors] = useState({});
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e) {
        e.preventDefault();
        setError(null); setFieldErrors({});
        try {
            await loginSchema.validate({ email, password }, { abortEarly: false });
            setLoading(true);
            const data = await api.login(email, password);
            localStorage.setItem("dojo_token", data.access_token);
            const user = await api.getMe();
            onLoginSuccess(user);
        } catch (err) {
            if (err.inner) {
                const errs = {};
                err.inner.forEach(({ path, message }) => { errs[path] = message; });
                setFieldErrors(errs);
            } else { setError(err.message || "Failed to log in"); }
        } finally { setLoading(false); }
    }


    return (
        <div className="flex flex-col items-center justify-center min-h-screen p-4">
            <div className="absolute top-6 left-6"><img src="/logo.jpg" alt="Dojo" className="h-12 w-auto rounded-md shadow-lg" /></div>
            <div className="w-full max-w-md space-y-8">
                <h1 className="text-4xl font-bold text-center text-white">Welcome to Dojo</h1>
                <p className="mt-2 text-center text-lg text-gray-400">Sign in to continue your training</p>
                {error && <ErrorMessage message={error} />}
                <form onSubmit={handleSubmit} className="space-y-6" noValidate>
                    <Input id="email" type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} error={fieldErrors.email} />
                    <Input id="password" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} error={fieldErrors.password} />
                    <Button type="submit" fullWidth isLoading={loading}>Sign In</Button>
                </form>
                <p className="text-center text-gray-400 mt-3">Not a member? <button className="text-indigo-400" onClick={() => navigateTo("register")}>Register now</button></p>
                <button
                    className="text-indigo-400 hover:underline mt-2 text-sm block mx-auto"
                    onClick={() => navigateTo("forgot-password")}
                >
                    Forgot password?
                </button>
            </div>
        </div>
    );
}

function RegisterPage({ navigateTo, onLoginSuccess }) {
    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [github_username, setGithubUsername] = useState("");
    const [error, setError] = useState(null);
    const [fieldErrors, setFieldErrors] = useState({});
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e) {
        e.preventDefault();
        setError(null); setFieldErrors({});
        try {
            await registerSchema.validate({ username, email, password, github_username }, { abortEarly: false });
            setLoading(true);
            await api.register(username, email, password, github_username);
            toast.success("Registered successfully! Logging you in...");
            const data = await api.login(email, password);
            localStorage.setItem("dojo_token", data.access_token);
            const user = await api.getMe();
            onLoginSuccess(user);
        } catch (err) {
            if (err.inner) {
                const errs = {};
                err.inner.forEach(({ path, message }) => { errs[path] = message; });
                setFieldErrors(errs);
            } else { setError(err.message || "Failed to register"); }
        } finally { setLoading(false); }
    }

    return (
        <div className="flex flex-col items-center justify-center min-h-screen p-4">
            <div className="absolute top-6 left-6"><img src="/logo.jpg" alt="Dojo" className="h-12 w-auto rounded-md shadow-lg" /></div>
            <div className="w-full max-w-md space-y-8">
                <h1 className="text-4xl font-bold text-center text-white">Join the Dojo</h1>
                <p className="mt-2 text-center text-lg text-gray-400">Create your account to start competing</p>
                {error && <ErrorMessage message={error} />}
                <form onSubmit={handleSubmit} className="space-y-6" noValidate>
                    <Input id="username" type="text" placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} error={fieldErrors.username} />
                    <Input id="email" type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} error={fieldErrors.email} />
                    <Input id="github_username" type="text" placeholder="GitHub Username" value={github_username} onChange={e => setGithubUsername(e.target.value)} error={fieldErrors.github_username} />
                    <Input id="password" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} error={fieldErrors.password} />
                    <Button type="submit" fullWidth isLoading={loading}>Create Account</Button>
                </form>
                <p className="text-center text-gray-400 mt-3">Already registered? <button className="text-indigo-400" onClick={() => navigateTo("login")}>Sign In</button></p>
            </div>
        </div>
    );
}

function ProfilePage({ navigateTo, user, onUserUpdate }) {
    const [githubUsername, setGithubUsername] = useState(user.github_username || "");
    const [error, setError] = useState(null);
    const [fieldErrors, setFieldErrors] = useState({});
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e) {
        e.preventDefault();
        setError(null); setFieldErrors({});
        try {
            await profileSchema.validate({ github_username: githubUsername }, { abortEarly: false });
            setLoading(true);
            const updatedUser = await api.updateMe(githubUsername);
            onUserUpdate(updatedUser);
            toast.success("Profile updated successfully!");
        } catch (err) {
            if (err.inner) {
                const errs = {};
                err.inner.forEach(({ path, message }) => { errs[path] = message; });
                setFieldErrors(errs);
            } else { setError(err.message || "Failed to update profile"); }
        } finally { setLoading(false); }
    }

    return (
        <div className="max-w-4xl mx-auto px-4 py-12">
            <button onClick={() => navigateTo("dashboard")} className="flex items-center text-indigo-400 hover:text-indigo-300 mb-6">
                <ArrowLeftIcon className="w-5 h-5 mr-2" /> Back to Dashboard
            </button>
            <h1 className="text-3xl font-bold text-white mb-4">Your Profile</h1>
            <p className="mb-6 text-gray-400">Update your details here. Your GitHub username is required to participate.</p>
            <div className="bg-gray-800 p-6 rounded-xl max-w-md">
                <form onSubmit={handleSubmit} className="space-y-6" noValidate>
                    <Input id="username" type="text" placeholder="Username" value={user.username} disabled />
                    <Input id="email" type="email" placeholder="Email" value={user.email} disabled />
                    <Input id="github_username" type="text" placeholder="GitHub Username" value={githubUsername} onChange={e => setGithubUsername(e.target.value)} error={fieldErrors.github_username || error} />
                    <div className="flex items-center space-x-4">
                        <Button type="submit" isLoading={loading}>Save Changes</Button>
                    </div>
                </form>
            </div>
        </div>
    );
}

function GroupProfilePage({ navigateTo, groupId, user }) {
    const [group, setGroup] = useState(null);
    const [leaderboard, setLeaderboard] = useState([]);
    const [challengeHistory, setChallengeHistory] = useState([]);
    const [submissions, setSubmissions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showChallengeForm, setShowChallengeForm] = useState(false);
    const [showFeedbackModal, setShowFeedbackModal] = useState(false);

    useEffect(() => { console.log(leaderboard) }, [leaderboard])

    const fetchData = useCallback(async () => {
        setError(null);
        try {
            const [groupData, leaderboardData, historyData, submissionsData] =
                await Promise.all([
                    api.getGroup(groupId),
                    api.getGroupLeaderboard(groupId),
                    api.getChallengeHistory(groupId),
                    api.getMySubmissions()
                ]);

            setGroup(groupData);
            setLeaderboard(leaderboardData || []);
            setChallengeHistory(historyData || []);
            setSubmissions(submissionsData || []);
        } catch (err) {
            setError(err.message || "Failed to load group data");
        } finally {
            setLoading(false);
        }
    }, [groupId]);

    useEffect(() => {
        const fetchOnce = async () => {
            setLoading(true);
            await fetchData();
            setLoading(false);
        };

        fetchOnce();
    }, [fetchData]);


    const getRowClass = (index) => {
        if (index === 0) return "bg-yellow-500/20 text-yellow-300";
        if (index === 1) return "bg-gray-500/20 text-gray-300";
        if (index === 2) return "bg-orange-800/40 text-orange-400";
        return "bg-gray-800/50";
    };

    if (loading) return <LoadingSpinner />;
    if (error) return <ErrorMessage message={error} onRetry={fetchData} />;
    if (!group) return <ErrorMessage message="Group not found." />;

    const userSubmissionsForGroup = submissions.filter(sub =>
        challengeHistory.some(ch => ch.id === sub.challenge_id)
    );

    return (
        <div className="max-w-4xl mx-auto px-4 py-12">
            <button onClick={() => navigateTo("dashboard")} className="flex items-center text-indigo-400 hover:text-indigo-300 mb-6"><ArrowLeftIcon className="w-5 h-5 mr-2" /> Back to All Groups</button>
            <div className="bg-gray-800 p-6 rounded-xl shadow">
                <h1 className="text-3xl text-white font-bold">{group.name}</h1>
                <p className="text-gray-400 mt-2">{group.description}</p>
                <p className="text-gray-500 text-xs mt-1">ID: {group.id}</p>
            </div>
            <div className="mt-6 flex justify-end">
                <Button onClick={() => setShowChallengeForm(true)}><PlusIcon className="w-5 h-5 mr-2" /> Create Challenge</Button>
            </div>

            {showChallengeForm && <CreateChallengeModal groupId={groupId} onClose={() => setShowChallengeForm(false)} onSuccess={fetchData} />}
            {showFeedbackModal && <FeedbackModal submissions={userSubmissionsForGroup} onClose={() => setShowFeedbackModal(false)} />}

            <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-10">
                <div>
                    <h2 className="text-2xl font-bold text-white mb-4">Leaderboard</h2>
                    {leaderboard.length === 0 ? (<p className="text-gray-400">No scores yet. Be the first!</p>) : (
                        <div className="overflow-x-auto rounded-lg border border-gray-700">
                            <table className="w-full table-auto text-left text-sm text-white">
                                <thead className="bg-gray-700 text-gray-300 uppercase"><tr><th className="px-4 py-3">Rank</th><th className="px-4 py-3">User</th><th className="px-4 py-3">XP</th></tr></thead>
                                <tbody className="divide-y divide-gray-700">
                                    {leaderboard.map((player, index) => (
                                        <tr key={player.user_id} className={getRowClass(index)}>
                                            <td className="px-4 py-3 font-bold">{index + 1}</td>
                                            <td className="px-4 py-3 flex items-center gap-2">
                                                <span>{player.username}</span>
                                                {player.user_id === user.id && <button onClick={() => setShowFeedbackModal(true)} title="View my feedback"><InfoIcon className="w-4 h-4 text-cyan-400" /></button>}
                                            </td>
                                            <td className="px-4 py-3">{player.score}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
                <div>
                    <h2 className="text-2xl font-bold text-white mb-4">Challenge History</h2>
                    {challengeHistory.length === 0 ? (<p className="text-gray-400">No challenges have been created yet.</p>) : (
                        <ul className="space-y-3">
                            {challengeHistory.map(ch => (
                                <li key={ch.id} className="bg-gray-800 p-3 rounded-lg flex justify-between items-center">
                                    <span className="font-semibold">{ch.Topic}</span>
                                    <span className="text-xs bg-gray-700 px-2 py-1 rounded-full">{ch.difficulty}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>
        </div>
    );
}

function Dashboard({ user, handleLogout, navigateTo }) {
    const [allGroups, setAllGroups] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showCreateModal, setShowCreateModal] = useState(false);

    async function fetchGroups() {
        setLoading(true); setError(null);
        try {
            const groups = await api.getGroups();
            setAllGroups(groups);
        } catch (err) {
            setError(err.message);
        } finally { setLoading(false); }
    }

    useEffect(() => { fetchGroups(); }, []);

    const myGroups = allGroups.filter(g => (g.members || []).includes(user.id));
    const otherGroups = allGroups.filter(g => !myGroups.some(myG => myG.id === g.id));

    return (
        <div className="max-w-7xl mx-auto px-4 py-12">
            <header className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white">Welcome, {user.username}</h1>
                    <p className="text-gray-400">Choose a group to get started</p>
                </div>
                <div className="flex gap-2 items-center">
                    <Button onClick={() => setShowCreateModal(true)}><PlusIcon className="mr-2 w-5 h-5" /> Create Group</Button>
                    <button onClick={() => navigateTo("profile")} title="Profile" className="p-2 rounded-full hover:bg-gray-700 transition-colors"><UserIcon className="w-6 h-6 text-gray-400" /></button>
                    <button onClick={handleLogout} title="Logout" className="p-2 rounded-full hover:bg-gray-700 transition-colors"><LogOutIcon className="w-6 h-6 text-gray-400" /></button>
                </div>
            </header>

            {loading && <LoadingSpinner />}
            {error && <ErrorMessage message={error} onRetry={fetchGroups} />}
            {!loading && !error && (
                <>
                    <section className="mb-10"><h2 className="text-2xl font-semibold text-white mb-4">My Groups</h2>
                        {myGroups.length === 0 ? (<p className="text-gray-400">You haven't joined any groups yet. Join one below!</p>) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">{myGroups.map(group => (<GroupCard key={group.id} group={group} onClick={() => navigateTo(`group:${group.id}`)} isJoined={true} fetchGroups={fetchGroups} />))}</div>
                        )}
                    </section>
                    <section><h2 className="text-2xl font-semibold text-white mb-4">All Groups</h2>
                        {otherGroups.length === 0 ? (<p className="text-gray-400">No other groups available to join.</p>) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">{otherGroups.map(group => (<GroupCard key={group.id} group={group} isJoined={false} fetchGroups={fetchGroups} />))}</div>
                        )}
                    </section>
                </>
            )}
            {showCreateModal && <CreateGroupModal onClose={() => setShowCreateModal(false)} onSuccess={fetchGroups} />}
        </div>
    );
}

function GroupCard({ group, onClick, isJoined, fetchGroups }) {
    const [loading, setLoading] = useState(false);
    async function handleJoinClick(e) {
        e.stopPropagation(); setLoading(true);
        try {
            await api.joinGroup(group.id);
            toast.success(`Successfully joined "${group.name}"!`);
            await fetchGroups();
        } catch (err) {
            toast.error(err.message || "Could not join group");
        } finally { setLoading(false); }
    }

    return (
        <div onClick={isJoined ? onClick : () => { }} className={`bg-gray-800 p-6 rounded-xl transition-all shadow-md relative ${isJoined ? 'cursor-pointer hover:bg-gray-700 hover:-translate-y-1' : ''}`}>
            <h3 className="text-xl font-bold text-white">{group.name}</h3>
            <p className="text-gray-400 mb-1 h-10 overflow-hidden">{group.description}</p>
            <p className="text-gray-500 text-xs mb-2">ID: {group.id}</p>
            <div className="flex items-center justify-between border-t border-gray-700 pt-3 text-sm text-gray-300">
                <span className="flex items-center"><UsersIcon className="w-4 h-4 mr-1" /> {group.members?.length || 0} Members</span>
                {!isJoined && <Button onClick={handleJoinClick} isLoading={loading} disabled={loading}>Join</Button>}
            </div>
        </div>
    );
}

// --- MODALS ---
function CreateGroupModal({ onClose, onSuccess }) {
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState({});

    async function handleSubmit(e) {
        e.preventDefault(); setErrors({});
        try {
            await createGroupSchema.validate({ name, description }, { abortEarly: false });
            setLoading(true);
            await api.createGroup(name, description);
            toast.success("Group created successfully!");
            onSuccess();
            onClose();
        } catch (err) {
            if (err.inner) {
                const errs = {};
                err.inner.forEach(({ path, message }) => { errs[path] = message; });
                setErrors(errs);
            } else { toast.error(err.message || "Failed to create group"); }
        } finally { setLoading(false); }
    }

    return (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 p-6 rounded-xl max-w-md w-full shadow-lg border border-gray-700">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl text-white font-bold">Create New Group</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white"><XIcon className="w-6 h-6" /></button>
                </div>
                <form onSubmit={handleSubmit} className="space-y-4" noValidate>
                    <Input id="name" type="text" placeholder="Group Name" value={name} onChange={e => setName(e.target.value)} error={errors.name} />
                    <Input id="description" type="text" placeholder="Description" value={description} onChange={e => setDescription(e.target.value)} error={errors.description} />
                    <div className="flex justify-end gap-4 pt-4">
                        <Button type="button" onClick={onClose} variant="secondary">Cancel</Button>
                        <Button type="submit" isLoading={loading}>Create</Button>
                    </div>
                </form>
            </div>
        </div>
    );
}

function CreateChallengeModal({ groupId, onClose, onSuccess }) {
    const [Topic, setTopic] = useState("");
    const [difficulty, setDifficulty] = useState("Easy");
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e) {
        e.preventDefault();
        try {
            await createChallengeSchema.validate({ Topic, difficulty });
            setLoading(true);
            await api.createChallenge(Topic, difficulty, groupId);
            toast.success("Challenge created! Members will be notified shortly.");
            onSuccess();
            onClose();
        } catch (err) {
            toast.error(err.message || "Failed to create challenge");
        } finally { setLoading(false); }
    }

    return (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 p-6 rounded-xl max-w-md w-full shadow-lg border border-gray-700">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-bold text-white">New Challenge</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white"><XIcon className="w-6 h-6" /></button>
                </div>
                <form onSubmit={handleSubmit} className="space-y-4" noValidate>
                    <Input id="Topic" type="text" placeholder="Challenge Topic (e.g., FastAPI, React)" value={Topic} onChange={(e) => setTopic(e.target.value)} required />
                    <div>
                        <label htmlFor="difficulty" className="block text-sm text-gray-300 mb-1">Difficulty</label>
                        <select id="difficulty" className="w-full p-3 rounded bg-gray-700 text-white border border-gray-600" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                            <option>Easy</option>
                            <option>Medium</option>
                            <option>Hard</option>
                        </select>
                    </div>
                    <div className="flex justify-end gap-4 pt-4">
                        <Button type="button" onClick={onClose} variant="secondary">Cancel</Button>
                        <Button type="submit" isLoading={loading}>Create</Button>
                    </div>
                </form>
            </div>
        </div>
    );
}

function FeedbackModal({ submissions, onClose }) {
    return (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 p-6 rounded-xl max-w-2xl w-full shadow-lg border border-gray-700">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl text-white font-bold">My Submission Feedback</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white"><XIcon className="w-6 h-6" /></button>
                </div>
                <div className="max-h-[60vh] overflow-y-auto pr-4 space-y-4">
                    {submissions.length > 0 ? submissions.map(sub => (
                        <div key={sub.id} className="bg-gray-900/50 p-4 rounded-lg">
                            <div className="flex justify-between items-center mb-2">
                                <p className="font-bold text-indigo-400">Commit: {sub.commit_hash.substring(0, 7)}</p>
                                <p className={`font-bold ${sub.score > 0 ? 'text-green-400' : 'text-red-400'}`}>Score: {sub.score}</p>
                            </div>
                            <p className="text-sm text-gray-300">{sub.feedback || "No feedback provided."}</p>
                        </div>
                    )) : (
                        <p className="text-gray-400 text-center py-8">You have no submissions for this group's challenges yet.</p>
                    )}
                </div>
            </div>
        </div>
    );
}

// Main App component
export default function App() {
    const [user, setUser] = useState(null);
    const [currentPage, setCurrentPage] = useState("login");
    const [currentGroupId, setCurrentGroupId] = useState(null);

    useEffect(() => {
        async function init() {
            const params = new URLSearchParams(window.location.search);
            const resetToken = params.get("token");

            // 🔐 If reset token exists, go to reset-password page
            if (resetToken) {
                setUser(null);
                setCurrentPage("reset-password");
                return;
            }

            const token = localStorage.getItem("dojo_token");
            if (!token) {
                setUser(null);
                setCurrentPage("login");
                return;
            }

            try {
                const userData = await api.getMe();
                setUser(userData);
                setCurrentPage("dashboard");
            } catch {
                localStorage.removeItem("dojo_token");
                setUser(null);
                setCurrentPage("login");
            }
        }
        init();
    }, []);


    function navigateTo(page) {
        if (page.startsWith("group:")) {
            setCurrentGroupId(page.split(":")[1]);
            setCurrentPage("group");
        } else {
            setCurrentGroupId(null);
            setCurrentPage(page);
        }
    }

    function onLoginSuccess(userData) {
        setUser(userData);
        setCurrentPage("dashboard");
    }

    function onUserUpdate(updated) {
        setUser(updated);
    }

    function handleLogout() {
        localStorage.removeItem("dojo_token");
        setUser(null);
        setCurrentPage("login");
    }

    function ForgotPassword({ navigateTo }) {
        const [email, setEmail] = useState("");
        const [message, setMessage] = useState("");

        async function handleSubmit(e) {
            e.preventDefault();
            try {
                await api.forgotPassword(email);
                setMessage("If the email exists, a reset link has been sent.");
            } catch {
                setMessage("If the email exists, a reset link has been sent.");
            }
        }

        return (
            <div className="flex items-center justify-center min-h-screen p-4">
                <form onSubmit={handleSubmit} className="bg-gray-800 p-6 rounded w-96">
                    <h2 className="text-xl text-white mb-4">Forgot Password</h2>

                    <Input
                        id="email"
                        type="email"
                        placeholder="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />

                    <Button type="submit" fullWidth>
                        Send Reset Link
                    </Button>

                    {message && (
                        <p className="text-gray-400 text-sm mt-3">{message}</p>
                    )}

                    <button
                        type="button"
                        onClick={() => navigateTo("login")}
                        className="text-indigo-400 mt-4 block"
                    >
                        Back to login
                    </button>
                </form>
            </div>
        );
    }



    function ResetPassword({ navigateTo }) {
        const params = new URLSearchParams(window.location.search);
        const token = params.get("token");
        const resetToken = params.get("token");
        if (resetToken) {
            setCurrentPage("reset-password");
        }
        const [password, setPassword] = useState("");
        const [message, setMessage] = useState("");

        async function handleSubmit(e) {
            e.preventDefault();
            try {
                await api.resetPassword(token, password);
                setMessage("Password reset successful. Redirecting...");
                setTimeout(() => navigateTo("login"), 1500);
            } catch {
                setMessage("Reset failed or token expired.");
            }
        }

        return (
            <div className="flex items-center justify-center min-h-screen p-4">
                <form onSubmit={handleSubmit} className="bg-gray-800 p-6 rounded w-96">
                    <h2 className="text-xl text-white mb-4">Reset Password</h2>

                    <Input
                        id="password"
                        type="password"
                        placeholder="New Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />

                    <Button type="submit" fullWidth>
                        Reset Password
                    </Button>

                    {message && (
                        <p className="text-gray-400 text-sm mt-3">{message}</p>
                    )}
                </form>
            </div>
        );
    }



    function renderPage() {
        // 🔓 User NOT logged in
        if (!user) {
            if (currentPage === "register") {
                return (
                    <RegisterPage
                        navigateTo={navigateTo}
                        onLoginSuccess={onLoginSuccess}
                    />
                );
            }

            if (currentPage === "forgot-password") {
                return <ForgotPassword navigateTo={navigateTo} />;
            }

            if (currentPage === "reset-password") {
                return <ResetPassword navigateTo={navigateTo} />;
            }

            // Default unauthenticated page
            return (
                <LoginPage
                    navigateTo={navigateTo}
                    onLoginSuccess={onLoginSuccess}
                />
            );
        }

        // 🔐 User logged in
        switch (currentPage) {
            case "profile":
                return (
                    <ProfilePage
                        navigateTo={navigateTo}
                        user={user}
                        onUserUpdate={onUserUpdate}
                    />
                );

            case "group":
                return (
                    <GroupProfilePage
                        navigateTo={navigateTo}
                        groupId={currentGroupId}
                        user={user}
                    />
                );

            case "dashboard":
            default:
                return (
                    <Dashboard
                        user={user}
                        handleLogout={handleLogout}
                        navigateTo={navigateTo}
                    />
                );
        }
    }



    return (
        <div className="bg-gray-900 text-white min-h-screen font-sans">
            {renderPage()}
            <ToastContainer position="bottom-center" autoClose={3000} hideProgressBar={false} newestOnTop={false} closeOnClick rtl={false} pauseOnFocusLoss draggable pauseOnHover theme="dark" />
        </div>
    )
}








