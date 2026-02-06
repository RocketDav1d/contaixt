"use client";

import { useState, useEffect } from "react";
import { Plus, MoreVertical, Pencil, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";

interface Vault {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  is_default: boolean;
  created_at: string;
  document_count?: number;
}

interface SourceConnection {
  id: string;
  source_type: string;
  nango_connection_id: string;
  status: string;
}

interface VaultConnection {
  id: string;
  source_type: string;
  nango_connection_id: string;
  status: string;
}

// Provider icons (simplified representations)
const ProviderIcon = ({ provider }: { provider: string }) => {
  const icons: Record<string, { bg: string; text: string }> = {
    gmail: { bg: "bg-red-500", text: "G" },
    notion: { bg: "bg-black", text: "N" },
    drive: { bg: "bg-green-500", text: "D" },
    slack: { bg: "bg-purple-500", text: "S" },
  };
  const icon = icons[provider] || { bg: "bg-gray-500", text: "?" };
  return (
    <div
      className={`flex h-5 w-5 items-center justify-center rounded-full ${icon.bg} text-[10px] font-bold text-white`}
    >
      {icon.text}
    </div>
  );
};

// Purple folder card component
function VaultCard({
  vault,
  connections,
  onEdit,
  onDelete,
  onManageConnections,
}: {
  vault: Vault;
  connections: VaultConnection[];
  onEdit: (vault: Vault) => void;
  onDelete: (vault: Vault) => void;
  onManageConnections: (vault: Vault) => void;
}) {
  return (
    <Card className="group relative overflow-hidden p-4 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5">
      {/* Folder Icon */}
      <div className="mb-4 flex justify-center">
        <div className="relative h-32 w-40">
          {/* Folder back */}
          <div className="absolute inset-x-0 top-4 h-28 rounded-xl bg-gradient-to-b from-[#412bcf] to-[#3623a8] shadow-sm" />
          {/* Folder tab */}
          <div className="absolute left-0 top-0 h-6 w-16 rounded-t-xl bg-[#412bcf]" />
          {/* Folder front */}
          <div className="absolute inset-x-0 top-8 h-24 rounded-xl bg-gradient-to-b from-[#6b5cd9] to-[#412bcf] shadow-inner" />

          {/* Provider icons at bottom */}
          <div className="absolute bottom-3 left-1/2 flex -translate-x-1/2 gap-1.5">
            {connections.slice(0, 3).map((conn) => (
              <ProviderIcon key={conn.id} provider={conn.source_type} />
            ))}
            {connections.length > 3 && (
              <div className="flex h-5 items-center rounded-full bg-white/90 px-1.5 text-[10px] font-medium text-gray-600 shadow-sm">
                +{connections.length - 3}
              </div>
            )}
            {connections.length === 0 && (
              <div className="flex h-5 items-center rounded-full bg-white/90 px-1.5 text-[10px] font-medium text-gray-400 shadow-sm">
                No sources
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Vault Info */}
      <div className="text-center">
        <h3 className="font-semibold">{vault.name}</h3>
        <p className="text-sm text-muted-foreground">
          {vault.document_count || 0} documents
        </p>
      </div>

      {/* Default Badge */}
      {vault.is_default && (
        <Badge
          variant="secondary"
          className="absolute right-2 top-2 text-xs"
        >
          Default
        </Badge>
      )}

      {/* Actions Menu */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-2 top-2 h-8 w-8 opacity-0 transition-opacity group-hover:opacity-100"
          >
            <MoreVertical className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => onManageConnections(vault)}>
            <Plus className="mr-2 h-4 w-4" />
            Manage connections
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => onEdit(vault)}>
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </DropdownMenuItem>
          {!vault.is_default && (
            <DropdownMenuItem
              className="text-destructive"
              onClick={() => onDelete(vault)}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </Card>
  );
}

export default function VaultsPage() {
  const [vaults, setVaults] = useState<Vault[]>([]);
  const [allConnections, setAllConnections] = useState<SourceConnection[]>([]);
  const [vaultConnections, setVaultConnections] = useState<Record<string, VaultConnection[]>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isManageConnectionsOpen, setIsManageConnectionsOpen] = useState(false);
  const [editingVault, setEditingVault] = useState<Vault | null>(null);
  const [managingVault, setManagingVault] = useState<Vault | null>(null);
  const [selectedConnectionIds, setSelectedConnectionIds] = useState<string[]>([]);
  const [createConnectionIds, setCreateConnectionIds] = useState<string[]>([]);
  const [formData, setFormData] = useState({ name: "", description: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // TODO: Get workspace_id from context
  const workspaceId = "50926c1f-8132-4694-bd8a-b250c4a67089";

  const fetchVaults = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/v1/vaults?workspace_id=${workspaceId}`
      );
      const data = await response.json();
      setVaults(data);
      // Fetch connections for each vault
      for (const vault of data) {
        await fetchVaultConnections(vault.id);
      }
    } catch (error) {
      console.error("Error fetching vaults:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAllConnections = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/v1/sources?workspace_id=${workspaceId}`
      );
      if (response.ok) {
        const data = await response.json();
        setAllConnections(data);
      }
    } catch (error) {
      console.error("Error fetching connections:", error);
    }
  };

  const fetchVaultConnections = async (vaultId: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/v1/vaults/${vaultId}/connections`
      );
      if (response.ok) {
        const data = await response.json();
        setVaultConnections((prev) => ({ ...prev, [vaultId]: data }));
      }
    } catch (error) {
      console.error("Error fetching vault connections:", error);
    }
  };

  useEffect(() => {
    fetchVaults();
    fetchAllConnections();
  }, []);

  const handleCreate = async () => {
    if (!formData.name.trim()) return;
    setIsSubmitting(true);

    try {
      const response = await fetch("http://localhost:8000/v1/vaults", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workspace_id: workspaceId,
          name: formData.name,
          description: formData.description || null,
        }),
      });

      if (response.ok) {
        const newVault = await response.json();

        // Assign selected connections to the new vault
        if (createConnectionIds.length > 0) {
          await fetch(
            `http://localhost:8000/v1/vaults/${newVault.id}/connections`,
            {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ connection_ids: createConnectionIds }),
            }
          );
        }

        setIsCreateOpen(false);
        setFormData({ name: "", description: "" });
        setCreateConnectionIds([]);
        fetchVaults();
      }
    } catch (error) {
      console.error("Error creating vault:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = async () => {
    if (!editingVault || !formData.name.trim()) return;
    setIsSubmitting(true);

    try {
      const response = await fetch(
        `http://localhost:8000/v1/vaults/${editingVault.id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: formData.name,
            description: formData.description || null,
          }),
        }
      );

      if (response.ok) {
        setIsEditOpen(false);
        setEditingVault(null);
        setFormData({ name: "", description: "" });
        fetchVaults();
      }
    } catch (error) {
      console.error("Error updating vault:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (vault: Vault) => {
    if (!confirm(`Are you sure you want to delete "${vault.name}"?`)) return;

    try {
      const response = await fetch(
        `http://localhost:8000/v1/vaults/${vault.id}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        fetchVaults();
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to delete vault");
      }
    } catch (error) {
      console.error("Error deleting vault:", error);
    }
  };

  const openEditDialog = (vault: Vault) => {
    setEditingVault(vault);
    setFormData({ name: vault.name, description: vault.description || "" });
    setIsEditOpen(true);
  };

  const openManageConnectionsDialog = (vault: Vault) => {
    setManagingVault(vault);
    const currentConnections = vaultConnections[vault.id] || [];
    setSelectedConnectionIds(currentConnections.map((c) => c.id));
    setIsManageConnectionsOpen(true);
  };

  const handleSaveConnections = async () => {
    if (!managingVault) return;
    setIsSubmitting(true);

    try {
      const response = await fetch(
        `http://localhost:8000/v1/vaults/${managingVault.id}/connections`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ connection_ids: selectedConnectionIds }),
        }
      );

      if (response.ok) {
        setIsManageConnectionsOpen(false);
        setManagingVault(null);
        await fetchVaultConnections(managingVault.id);
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to update connections");
      }
    } catch (error) {
      console.error("Error updating connections:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleConnection = (connectionId: string) => {
    setSelectedConnectionIds((prev) =>
      prev.includes(connectionId)
        ? prev.filter((id) => id !== connectionId)
        : [...prev, connectionId]
    );
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Context vaults</h1>
          <p className="text-muted-foreground">
            Organize your data into separate contexts
          </p>
        </div>

        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button className="bg-[#412bcf] hover:bg-[#3623a8]">
              <Plus className="mr-2 h-4 w-4" />
              New
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Create new vault</DialogTitle>
              <DialogDescription>
                Create a new context vault to organize your data.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium">Name</label>
                <Input
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  placeholder="e.g., Sales, Engineering, Operations"
                />
              </div>
              <div>
                <label className="text-sm font-medium">
                  Description (optional)
                </label>
                <Textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  placeholder="What is this vault for?"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Data sources</label>
                <p className="text-xs text-muted-foreground mb-2">
                  Select which integrations this vault should have access to.
                </p>
                <div className="space-y-2 max-h-[200px] overflow-y-auto border rounded-lg p-2">
                  {allConnections.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-4">
                      No connections available. Add integrations first.
                    </p>
                  ) : (
                    allConnections.map((connection) => (
                      <div
                        key={connection.id}
                        className="flex items-center space-x-3 rounded-lg p-2 hover:bg-muted/50 cursor-pointer"
                        onClick={() => {
                          setCreateConnectionIds((prev) =>
                            prev.includes(connection.id)
                              ? prev.filter((id) => id !== connection.id)
                              : [...prev, connection.id]
                          );
                        }}
                      >
                        <Checkbox
                          checked={createConnectionIds.includes(connection.id)}
                          onCheckedChange={() => {
                            setCreateConnectionIds((prev) =>
                              prev.includes(connection.id)
                                ? prev.filter((id) => id !== connection.id)
                                : [...prev, connection.id]
                            );
                          }}
                        />
                        <ProviderIcon provider={connection.source_type} />
                        <div className="flex-1">
                          <p className="text-sm font-medium capitalize">
                            {connection.source_type}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {connection.nango_connection_id}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setIsCreateOpen(false);
                  setCreateConnectionIds([]);
                }}
              >
                Cancel
              </Button>
              <Button onClick={handleCreate} disabled={isSubmitting}>
                {isSubmitting && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Create vault
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Vaults Grid */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : vaults.length === 0 ? (
        <div className="flex h-64 items-center justify-center text-muted-foreground">
          <div className="text-center">
            <p className="text-lg font-medium">No vaults yet</p>
            <p className="text-sm">Create your first context vault to get started.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {vaults.map((vault) => (
            <VaultCard
              key={vault.id}
              vault={vault}
              connections={vaultConnections[vault.id] || []}
              onEdit={openEditDialog}
              onDelete={handleDelete}
              onManageConnections={openManageConnectionsDialog}
            />
          ))}
        </div>
      )}

      {/* Edit Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit vault</DialogTitle>
            <DialogDescription>
              Update the vault name and description.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium">Name</label>
              <Input
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
              />
            </div>
            <div>
              <label className="text-sm font-medium">
                Description (optional)
              </label>
              <Textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleEdit} disabled={isSubmitting}>
              {isSubmitting && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Save changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Manage Connections Dialog */}
      <Dialog open={isManageConnectionsOpen} onOpenChange={setIsManageConnectionsOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Manage connections</DialogTitle>
            <DialogDescription>
              Select which data sources should be accessible in &quot;{managingVault?.name}&quot;.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-4 max-h-[300px] overflow-y-auto">
            {allConnections.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No connections available. Add integrations first.
              </p>
            ) : (
              allConnections.map((connection) => (
                <div
                  key={connection.id}
                  className="flex items-center space-x-3 rounded-lg border p-3 hover:bg-muted/50 cursor-pointer"
                  onClick={() => toggleConnection(connection.id)}
                >
                  <Checkbox
                    checked={selectedConnectionIds.includes(connection.id)}
                    onCheckedChange={() => toggleConnection(connection.id)}
                  />
                  <ProviderIcon provider={connection.source_type} />
                  <div className="flex-1">
                    <p className="text-sm font-medium capitalize">
                      {connection.source_type}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {connection.nango_connection_id}
                    </p>
                  </div>
                  <Badge
                    variant={connection.status === "active" ? "default" : "secondary"}
                    className={
                      connection.status === "active"
                        ? "bg-[#412bcf]/10 text-[#412bcf]"
                        : ""
                    }
                  >
                    {connection.status}
                  </Badge>
                </div>
              ))
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsManageConnectionsOpen(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleSaveConnections} disabled={isSubmitting}>
              {isSubmitting && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
