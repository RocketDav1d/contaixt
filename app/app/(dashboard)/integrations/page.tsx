"use client";

import { useState, useEffect } from "react";
import { Plus, RefreshCw, Loader2, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";

interface SourceConnection {
  id: string;
  workspace_id: string;
  vault_id: string;
  source_type: string;
  nango_connection_id: string;
  external_account_id: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

interface Vault {
  id: string;
  name: string;
}

// Provider configurations
const PROVIDERS = {
  gmail: {
    name: "Gmail",
    icon: (
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-100">
        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="#EA4335">
          <path d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z" />
        </svg>
      </div>
    ),
    color: "bg-red-500",
  },
  notion: {
    name: "Notion",
    icon: (
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gray-100">
        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="#000">
          <path d="M4.459 4.208c.746.606 1.026.56 2.428.466l13.215-.793c.28 0 .047-.28-.046-.326L17.86 1.968c-.42-.326-.981-.7-2.055-.607L3.01 2.295c-.466.046-.56.28-.374.466l1.823 1.447zm.793 3.08v13.904c0 .747.373 1.027 1.214.98l14.523-.84c.841-.046.935-.56.935-1.167V6.354c0-.606-.233-.933-.748-.887l-15.177.887c-.56.047-.747.327-.747.934zm14.337.745c.093.42 0 .84-.42.888l-.7.14v10.264c-.608.327-1.168.514-1.635.514-.748 0-.935-.234-1.495-.933l-4.577-7.186v6.952l1.448.327s0 .84-1.168.84l-3.222.186c-.093-.186 0-.653.327-.746l.84-.233V9.854L7.822 9.62c-.094-.42.14-1.026.793-1.073l3.456-.233 4.764 7.279v-6.44l-1.215-.14c-.093-.514.28-.887.747-.933l3.222-.187zM2.1 1.155L16.055.14C17.875-.047 18.414 0 19.682.933l4.064 2.8c.84.607 1.12 1.167 1.12 2.334v15.503c0 1.26-.467 2.007-2.1 2.1l-15.457.887c-1.26.047-1.867-.14-2.521-.98L1.355 19.58C.635 18.647.4 17.947.4 16.86V3.162c0-1.12.466-2.053 1.7-2.007z" />
        </svg>
      </div>
    ),
    color: "bg-gray-900",
  },
  drive: {
    name: "Google Drive",
    icon: (
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100">
        <svg className="h-5 w-5" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M12 11L6 21h12l-6-10z" />
          <path fill="#FBBC05" d="M6 21l3.5-6H2l4 6z" />
          <path fill="#34A853" d="M14.5 15H22l-4-6H9.5l5 6z" />
          <path fill="#EA4335" d="M12 3L6 13h6l6-10H12z" />
        </svg>
      </div>
    ),
    color: "bg-blue-500",
  },
  slack: {
    name: "Slack",
    icon: (
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-100">
        <svg className="h-5 w-5" viewBox="0 0 24 24">
          <path
            fill="#E01E5A"
            d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313z"
          />
          <path
            fill="#36C5F0"
            d="M8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312z"
          />
          <path
            fill="#2EB67D"
            d="M18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312z"
          />
          <path
            fill="#ECB22E"
            d="M15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"
          />
        </svg>
      </div>
    ),
    color: "bg-purple-500",
  },
};

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} minutes ago`;
  if (diffHours < 24) return `${diffHours} hours ago`;
  if (diffDays === 1) return "Yesterday";
  return `${diffDays} days ago`;
}

export default function IntegrationsPage() {
  const [connections, setConnections] = useState<SourceConnection[]>([]);
  const [vaults, setVaults] = useState<Vault[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState("");
  const [selectedVault, setSelectedVault] = useState("");
  const [connectionId, setConnectionId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [syncingId, setSyncingId] = useState<string | null>(null);

  // TODO: Get workspace_id from context
  const workspaceId = "50926c1f-8132-4694-bd8a-b250c4a67089";

  const fetchConnections = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/v1/sources?workspace_id=${workspaceId}`
      );
      if (response.ok) {
        const data = await response.json();
        setConnections(data);
      }
    } catch (error) {
      console.error("Error fetching connections:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchVaults = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/v1/vaults?workspace_id=${workspaceId}`
      );
      if (response.ok) {
        const data = await response.json();
        setVaults(data);
        // Set default vault as initial selection
        const defaultVault = data.find((v: Vault) => v.name === "Default");
        if (defaultVault) {
          setSelectedVault(defaultVault.id);
        }
      }
    } catch (error) {
      console.error("Error fetching vaults:", error);
    }
  };

  useEffect(() => {
    fetchConnections();
    fetchVaults();
  }, []);

  const handleAddConnection = async () => {
    if (!selectedProvider || !connectionId.trim()) return;
    setIsSubmitting(true);

    try {
      const response = await fetch(
        "http://localhost:8000/v1/sources/nango/register",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            workspace_id: workspaceId,
            source_type: selectedProvider,
            nango_connection_id: connectionId,
            vault_id: selectedVault || undefined,
          }),
        }
      );

      if (response.ok) {
        setIsAddOpen(false);
        setSelectedProvider("");
        setConnectionId("");
        fetchConnections();
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to add connection");
      }
    } catch (error) {
      console.error("Error adding connection:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBackfill = async (sourceType: string) => {
    setSyncingId(sourceType);
    try {
      const response = await fetch(
        `http://localhost:8000/v1/sources/${sourceType}/backfill`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ workspace_id: workspaceId }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        alert(`Backfill started: ${data.documents_ingested || 0} documents queued`);
      } else {
        const error = await response.json();
        alert(error.detail || "Backfill failed");
      }
    } catch (error) {
      console.error("Error triggering backfill:", error);
    } finally {
      setSyncingId(null);
    }
  };

  const getVaultName = (vaultId: string) => {
    const vault = vaults.find((v) => v.id === vaultId);
    return vault?.name || "Unknown";
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Integrations</h1>
          <p className="text-muted-foreground">
            Connect your data sources to Contaixt
          </p>
        </div>

        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogTrigger asChild>
            <Button className="bg-emerald-600 hover:bg-emerald-700">
              <Plus className="mr-2 h-4 w-4" />
              Add integration
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add new integration</DialogTitle>
              <DialogDescription>
                Connect a new data source via Nango.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium">Provider</label>
                <Select
                  value={selectedProvider}
                  onValueChange={setSelectedProvider}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a provider" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(PROVIDERS).map(([key, provider]) => (
                      <SelectItem key={key} value={key}>
                        <div className="flex items-center gap-2">
                          {provider.icon}
                          <span>{provider.name}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">
                  Nango Connection ID
                </label>
                <Input
                  value={connectionId}
                  onChange={(e) => setConnectionId(e.target.value)}
                  placeholder="Enter your Nango connection ID"
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  Get this from your Nango dashboard after connecting.
                </p>
              </div>
              <div>
                <label className="text-sm font-medium">Target Vault</label>
                <Select value={selectedVault} onValueChange={setSelectedVault}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a vault" />
                  </SelectTrigger>
                  <SelectContent>
                    {vaults.map((vault) => (
                      <SelectItem key={vault.id} value={vault.id}>
                        {vault.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsAddOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddConnection} disabled={isSubmitting}>
                {isSubmitting && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Add integration
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Connections Table */}
      <Card>
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : connections.length === 0 ? (
          <div className="flex h-64 items-center justify-center text-muted-foreground">
            <div className="text-center">
              <p className="text-lg font-medium">No integrations yet</p>
              <p className="text-sm">
                Add your first data source to get started.
              </p>
            </div>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Data source</TableHead>
                <TableHead>Vault</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last sync</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {connections.map((connection) => {
                const provider =
                  PROVIDERS[connection.source_type as keyof typeof PROVIDERS];
                return (
                  <TableRow key={connection.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        {provider?.icon || (
                          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gray-100">
                            ?
                          </div>
                        )}
                        <div>
                          <p className="font-medium">
                            {provider?.name || connection.source_type}{" "}
                            connection
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {connection.nango_connection_id}
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {getVaultName(connection.vault_id)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          connection.status === "active"
                            ? "default"
                            : "secondary"
                        }
                        className={
                          connection.status === "active"
                            ? "bg-emerald-100 text-emerald-700"
                            : ""
                        }
                      >
                        {connection.status === "active" ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatRelativeTime(connection.updated_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleBackfill(connection.source_type)}
                        disabled={syncingId === connection.source_type}
                      >
                        {syncingId === connection.source_type ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <RefreshCw className="mr-2 h-4 w-4" />
                        )}
                        Sync
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
