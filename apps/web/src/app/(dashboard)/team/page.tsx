"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { api } from "@/lib/api";
import type { TeamMember } from "@/types";

export default function TeamPage() {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [teamName, setTeamName] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("editor");
  const [loading, setLoading] = useState(true);
  const [inviteOpen, setInviteOpen] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get("/teams/current"),
      api.get("/teams/current/members"),
    ]).then(([teamRes, membersRes]) => {
      setTeamName(teamRes.data.team.name);
      setMembers(membersRes.data.members || []);
      setLoading(false);
    });
  }, []);

  const handleInvite = async () => {
    try {
      await api.post("/teams/current/invites", { email: inviteEmail, role: inviteRole });
      setInviteOpen(false);
      setInviteEmail("");
      const res = await api.get("/teams/current/members");
      setMembers(res.data.members || []);
    } catch (e) {
      console.error("Invite failed:", e);
    }
  };

  const handleRemove = async (userId: string) => {
    if (!confirm("Remove this member?")) return;
    await api.delete(`/teams/current/members/${userId}`);
    setMembers(members.filter((m) => m.user_id !== userId));
  };

  if (loading) return <p className="text-gray-400">Loading...</p>;

  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">Team Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>Team Name</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-3">
          <Input value={teamName} onChange={(e) => setTeamName(e.target.value)} />
          <Button onClick={() => api.patch("/teams/current", { name: teamName })}>Save</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Members ({members.length})</CardTitle>
          <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
            <DialogTrigger asChild>
              <Button size="sm">Invite Member</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Invite Team Member</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 mt-4">
                <Input placeholder="Email address" value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} />
                <Select value={inviteRole} onValueChange={setInviteRole}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="editor">Editor</SelectItem>
                    <SelectItem value="viewer">Viewer</SelectItem>
                  </SelectContent>
                </Select>
                <Button onClick={handleInvite} className="w-full">Send Invitation</Button>
              </div>
            </DialogContent>
          </Dialog>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Member</TableHead>
                <TableHead>Role</TableHead>
                <TableHead className="w-[100px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {members.map((m) => (
                <TableRow key={m.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <Avatar className="h-8 w-8">
                        <AvatarFallback>{m.user_name?.charAt(0)?.toUpperCase() || "?"}</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium">{m.user_name || m.user_email}</p>
                        <p className="text-xs text-gray-400">{m.user_email}</p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell><Badge variant={m.role === "owner" ? "default" : "secondary"}>{m.role}</Badge></TableCell>
                  <TableCell>
                    {m.role !== "owner" && (
                      <Button variant="ghost" size="sm" onClick={() => handleRemove(m.user_id)}>Remove</Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
