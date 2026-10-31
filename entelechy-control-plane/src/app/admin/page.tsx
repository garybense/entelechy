"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

type User = {
  id: string;
  username: string;
  display_name: string | null;
  org: string | null;
  role: "user" | "admin";
  disabled: boolean;
  created_at: string;
  bank_count?: number;
  key_count?: number;
};
type Key = { id: string; name: string; prefix: string; created_at: string; last_used_at: string | null; revoked_at: string | null };
type UserDetail = User & { keys: Key[]; banks: string[] };
type Owner = { bank_id: string; user_id: string; username: string; created_at: string };

async function api<T = unknown>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api/admin/${path}`, {
    ...init,
    headers: init?.body ? { "Content-Type": "application/json" } : undefined,
  });
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  let data: unknown = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    /* non-JSON error body */
  }
  if (!res.ok) {
    const detail = (data as { detail?: unknown }).detail;
    throw new Error(typeof detail === "string" ? detail : `Request failed (${res.status})`);
  }
  return data as T;
}

const fmt = (s: string | null) => (s ? new Date(s).toLocaleString() : "never");

export default function AdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [owners, setOwners] = useState<Owner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [newOpen, setNewOpen] = useState(false);
  const [form, setForm] = useState({ username: "", display_name: "", org: "", role: "user" });

  const [detail, setDetail] = useState<UserDetail | null>(null);
  const [newKeyName, setNewKeyName] = useState("");
  const [shownKey, setShownKey] = useState<string | null>(null);

  const [ownerBank, setOwnerBank] = useState("");
  const [ownerUser, setOwnerUser] = useState("");

  const load = useCallback(async () => {
    try {
      const [u, o] = await Promise.all([
        api<{ users: User[] }>("users"),
        api<{ owners: Owner[] }>("banks"),
      ]);
      setUsers(u.users);
      setOwners(o.owners);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const openDetail = async (id: string) => {
    try {
      setDetail(await api<UserDetail>(`users/${id}`));
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed");
    }
  };

  const run = async (fn: () => Promise<unknown>, ok: string, refreshDetail?: string) => {
    try {
      await fn();
      toast.success(ok);
      await load();
      if (refreshDetail) await openDetail(refreshDetail);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed");
    }
  };

  const createUser = () =>
    run(async () => {
      await api("users", {
        method: "POST",
        body: JSON.stringify({
          username: form.username.trim(),
          display_name: form.display_name.trim() || null,
          org: form.org.trim() || null,
          role: form.role,
        }),
      });
      setNewOpen(false);
      setForm({ username: "", display_name: "", org: "", role: "user" });
    }, "User created");

  const createKey = async () => {
    if (!detail) return;
    try {
      const k = await api<{ key: string }>(`users/${detail.id}/keys`, {
        method: "POST",
        body: JSON.stringify({ name: newKeyName.trim() || "default" }),
      });
      setShownKey(k.key);
      setNewKeyName("");
      await load();
      await openDetail(detail.id);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed");
    }
  };

  return (
    <div className="min-h-screen bg-background p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Administration</h1>
        <Link href="/dashboard" className="text-sm text-muted-foreground hover:underline">
          Back to dashboard
        </Link>
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-destructive/50 p-3 text-sm text-destructive">
          {error}. The admin API needs the multi-user extension enabled on the API service.
        </div>
      )}

      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users">Users ({users.length})</TabsTrigger>
          <TabsTrigger value="banks">Bank owners ({owners.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="users" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setNewOpen(true)}>New user</Button>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Username</TableHead>
                <TableHead>Organization</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Banks</TableHead>
                <TableHead>Keys</TableHead>
                <TableHead>Status</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">
                    {u.username}
                    {u.display_name ? <span className="text-muted-foreground"> ({u.display_name})</span> : null}
                  </TableCell>
                  <TableCell>{u.org || "-"}</TableCell>
                  <TableCell>{u.role}</TableCell>
                  <TableCell>{u.bank_count ?? 0}</TableCell>
                  <TableCell>{u.key_count ?? 0}</TableCell>
                  <TableCell>{u.disabled ? "disabled" : "active"}</TableCell>
                  <TableCell className="text-right space-x-2">
                    <Button size="sm" variant="outline" onClick={() => openDetail(u.id)}>
                      Manage
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        run(
                          () => api(`users/${u.id}`, { method: "PATCH", body: JSON.stringify({ disabled: !u.disabled }) }),
                          u.disabled ? "User enabled" : "User disabled"
                        )
                      }
                    >
                      {u.disabled ? "Enable" : "Disable"}
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => {
                        if (window.confirm(`Delete ${u.username}? Their keys and bank ownership records are removed (bank data stays, owned by nobody).`))
                          run(() => api(`users/${u.id}`, { method: "DELETE" }), "User deleted");
                      }}
                    >
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!loading && users.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-muted-foreground">
                    No users yet.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="banks" className="space-y-4">
          <div className="flex flex-wrap items-end gap-2">
            <div>
              <Label htmlFor="ob">Bank id</Label>
              <Input id="ob" value={ownerBank} onChange={(e) => setOwnerBank(e.target.value)} placeholder="bank id" />
            </div>
            <div>
              <Label htmlFor="ou">Owner</Label>
              <select
                id="ou"
                className="h-9 rounded-md border border-input bg-background px-3 text-sm"
                value={ownerUser}
                onChange={(e) => setOwnerUser(e.target.value)}
              >
                <option value="">Select user</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.username}
                  </option>
                ))}
              </select>
            </div>
            <Button
              disabled={!ownerBank.trim() || !ownerUser}
              onClick={() =>
                run(
                  () => api(`banks/${encodeURIComponent(ownerBank.trim())}/owner`, { method: "PUT", body: JSON.stringify({ user_id: ownerUser }) }),
                  "Owner set"
                ).then(() => setOwnerBank(""))
              }
            >
              Assign / transfer
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">
            Banks not listed here have no owner: only the admin can reach them. Assigning a bank gives that user full access to it.
          </p>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Bank</TableHead>
                <TableHead>Owner</TableHead>
                <TableHead>Since</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {owners.map((o) => (
                <TableRow key={o.bank_id}>
                  <TableCell className="font-medium">{o.bank_id}</TableCell>
                  <TableCell>{o.username}</TableCell>
                  <TableCell>{fmt(o.created_at)}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => run(() => api(`banks/${encodeURIComponent(o.bank_id)}/owner`, { method: "DELETE" }), "Ownership released")}
                    >
                      Release
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!loading && owners.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-muted-foreground">
                    No owned banks yet.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>

      <Dialog open={newOpen} onOpenChange={setNewOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New user</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <Label htmlFor="nu">Username</Label>
              <Input id="nu" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
            </div>
            <div>
              <Label htmlFor="nd">Display name</Label>
              <Input id="nd" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
            </div>
            <div>
              <Label htmlFor="no">Organization</Label>
              <Input id="no" value={form.org} onChange={(e) => setForm({ ...form, org: e.target.value })} />
            </div>
            <div>
              <Label htmlFor="nr">Role</Label>
              <select
                id="nr"
                className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
              >
                <option value="user">user (own banks only)</option>
                <option value="admin">admin (all banks, user management)</option>
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button disabled={!form.username.trim()} onClick={createUser}>
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={!!detail}
        onOpenChange={(o) => {
          if (!o) {
            setDetail(null);
            setShownKey(null);
          }
        }}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{detail?.username}</DialogTitle>
          </DialogHeader>
          {detail && (
            <div className="space-y-4">
              {shownKey && (
                <div className="rounded-md border p-3 text-sm space-y-2">
                  <div className="font-medium">New API key (shown once, copy it now)</div>
                  <code className="block break-all rounded bg-muted p-2">{shownKey}</code>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => navigator.clipboard.writeText(shownKey).then(() => toast.success("Copied"))}
                  >
                    Copy
                  </Button>
                </div>
              )}
              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <Label htmlFor="kn">New key name</Label>
                  <Input id="kn" value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)} placeholder="e.g. laptop" />
                </div>
                <Button onClick={createKey}>Create key</Button>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Key</TableHead>
                    <TableHead>Last used</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {detail.keys.map((k) => (
                    <TableRow key={k.id}>
                      <TableCell>{k.name}</TableCell>
                      <TableCell className="font-mono">{k.prefix}...</TableCell>
                      <TableCell>{fmt(k.last_used_at)}</TableCell>
                      <TableCell>{k.revoked_at ? "revoked" : "active"}</TableCell>
                      <TableCell className="text-right">
                        {!k.revoked_at && (
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => run(() => api(`keys/${k.id}`, { method: "DELETE" }), "Key revoked (takes effect within 30 s)", detail.id)}
                          >
                            Revoke
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  {detail.keys.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-muted-foreground">
                        No keys.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
              <div className="text-sm text-muted-foreground">
                Banks: {detail.banks.length ? detail.banks.join(", ") : "none"}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
