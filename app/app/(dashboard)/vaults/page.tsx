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

interface Vault {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  is_default: boolean;
  created_at: string;
  document_count?: number;
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
  onEdit,
  onDelete,
}: {
  vault: Vault;
  onEdit: (vault: Vault) => void;
  onDelete: (vault: Vault) => void;
}) {
  return (
    <Card className="group relative overflow-hidden p-4 transition-shadow hover:shadow-md">
      {/* Folder Icon */}
      <div className="mb-4 flex justify-center">
        <div className="relative h-32 w-40">
          {/* Folder back */}
          <div className="absolute inset-x-0 top-4 h-28 rounded-lg bg-gradient-to-b from-violet-400 to-violet-500" />
          {/* Folder tab */}
          <div className="absolute left-0 top-0 h-6 w-16 rounded-t-lg bg-violet-400" />
          {/* Folder front */}
          <div className="absolute inset-x-0 top-8 h-24 rounded-lg bg-gradient-to-b from-violet-300 to-violet-400" />

          {/* Provider icons at bottom */}
          <div className="absolute bottom-2 left-1/2 flex -translate-x-1/2 gap-1">
            <ProviderIcon provider="gmail" />
            <ProviderIcon provider="notion" />
            {vault.document_count && vault.document_count > 2 && (
              <div className="flex h-5 items-center rounded-full bg-gray-200 px-1.5 text-[10px] font-medium text-gray-600">
                +{vault.document_count - 2}
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
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editingVault, setEditingVault] = useState<Vault | null>(null);
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
    } catch (error) {
      console.error("Error fetching vaults:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchVaults();
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
        setIsCreateOpen(false);
        setFormData({ name: "", description: "" });
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
            <Button className="bg-emerald-600 hover:bg-emerald-700">
              <Plus className="mr-2 h-4 w-4" />
              New
            </Button>
          </DialogTrigger>
          <DialogContent>
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
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsCreateOpen(false)}
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
              onEdit={openEditDialog}
              onDelete={handleDelete}
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
    </div>
  );
}
