"use client";

import { useState, useEffect, useCallback } from "react";
import Nango from "@nangohq/frontend";
import { Plus, RefreshCw, Loader2, Trash2 } from "lucide-react";
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface SourceConnection {
  id: string;
  workspace_id: string;
  vault_ids: string[];
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
const PROVIDERS: Record<
  string,
  { name: string; icon: React.ReactNode; nangoKey: string }
> = {
  gmail: {
    name: "Gmail",
    nangoKey: "google-mail",
    icon: (
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-100">
        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="#EA4335">
          <path d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z" />
        </svg>
      </div>
    ),
  },
  notion: {
    name: "Notion",
    nangoKey: "notion",
    icon: (
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gray-100">
        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="#000">
          <path d="M4.459 4.208c.746.606 1.026.56 2.428.466l13.215-.793c.28 0 .047-.28-.046-.326L17.86 1.968c-.42-.326-.981-.7-2.055-.607L3.01 2.295c-.466.046-.56.28-.374.466l1.823 1.447zm.793 3.08v13.904c0 .747.373 1.027 1.214.98l14.523-.84c.841-.046.935-.56.935-1.167V6.354c0-.606-.233-.933-.748-.887l-15.177.887c-.56.047-.747.327-.747.934zm14.337.745c.093.42 0 .84-.42.888l-.7.14v10.264c-.608.327-1.168.514-1.635.514-.748 0-.935-.234-1.495-.933l-4.577-7.186v6.952l1.448.327s0 .84-1.168.84l-3.222.186c-.093-.186 0-.653.327-.746l.84-.233V9.854L7.822 9.62c-.094-.42.14-1.026.793-1.073l3.456-.233 4.764 7.279v-6.44l-1.215-.14c-.093-.514.28-.887.747-.933l3.222-.187zM2.1 1.155L16.055.14C17.875-.047 18.414 0 19.682.933l4.064 2.8c.84.607 1.12 1.167 1.12 2.334v15.503c0 1.26-.467 2.007-2.1 2.1l-15.457.887c-1.26.047-1.867-.14-2.521-.98L1.355 19.58C.635 18.647.4 17.947.4 16.86V3.162c0-1.12.466-2.053 1.7-2.007z" />
        </svg>
      </div>
    ),
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

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function IntegrationsPage() {
  const [connections, setConnections] = useState<SourceConnection[]>([]);
  const [vaults, setVaults] = useState<Vault[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [deleteConnection, setDeleteConnection] =
    useState<SourceConnection | null>(null);

  // TODO: Get from auth context
  const workspaceId = "50926c1f-8132-4694-bd8a-b250c4a67089";
  const userId = "user-1"; // Should come from Supabase auth

  const fetchConnections = useCallback(async () => {
    try {
      const response = await fetch(
        `${API_URL}/v1/sources?workspace_id=${workspaceId}`
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
  }, [workspaceId]);

  const fetchVaults = useCallback(async () => {
    try {
      const response = await fetch(
        `${API_URL}/v1/vaults?workspace_id=${workspaceId}`
      );
      if (response.ok) {
        const data = await response.json();
        setVaults(data);
      }
    } catch (error) {
      console.error("Error fetching vaults:", error);
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchConnections();
    fetchVaults();
  }, [fetchConnections, fetchVaults]);

  const handleAddIntegration = async () => {
    setIsConnecting(true);

    try {
      // 1. Get connect session token from backend
      const sessionResponse = await fetch(
        `${API_URL}/v1/sources/nango/connect-session`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            workspace_id: workspaceId,
            user_id: userId,
          }),
        }
      );

      if (!sessionResponse.ok) {
        const error = await sessionResponse.json();
        throw new Error(error.detail || "Failed to create session");
      }

      const { token } = await sessionResponse.json();

      // 2. Initialize Nango with the session token
      const nango = new Nango({ connectSessionToken: token });

      // 3. Open Nango Connect UI
      nango.openConnectUI({
        onEvent: (event) => {
          console.log("Nango event:", event);

          if (event.type === "close") {
            setIsConnecting(false);
            // Refresh connections after modal closes
            // (webhook may have created the connection)
            setTimeout(() => fetchConnections(), 1000);
          }

          if (event.type === "connect") {
            // Connection created successfully
            console.log("Connected:", event.payload);
            fetchConnections();
          }
        },
      });
    } catch (error) {
      console.error("Error starting connection:", error);
      alert(
        error instanceof Error ? error.message : "Failed to start connection"
      );
      setIsConnecting(false);
    }
  };

  const handleBackfill = async (sourceType: string) => {
    setSyncingId(sourceType);
    try {
      const response = await fetch(
        `${API_URL}/v1/sources/${sourceType}/backfill`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ workspace_id: workspaceId }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        alert(
          `Backfill complete: ${data.ingested} documents ingested from ${data.fetched} records`
        );
        fetchConnections();
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

  const handleDelete = async () => {
    if (!deleteConnection) return;

    try {
      const response = await fetch(
        `${API_URL}/v1/sources/${deleteConnection.id}`,
        {
          method: "DELETE",
        }
      );

      if (response.ok) {
        fetchConnections();
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to delete connection");
      }
    } catch (error) {
      console.error("Error deleting connection:", error);
    } finally {
      setDeleteConnection(null);
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

        <Button
          onClick={handleAddIntegration}
          disabled={isConnecting}
          className="bg-[#412bcf] hover:bg-[#3623a8]"
        >
          {isConnecting ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Plus className="mr-2 h-4 w-4" />
          )}
          Add integration
        </Button>
      </div>

      {/* Info Card */}
      <Card className="mb-6 border-blue-200 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-950">
        <p className="text-sm text-blue-800 dark:text-blue-200">
          Click &quot;Add integration&quot; to connect Gmail, Notion, or other
          data sources. After connecting, click &quot;Sync&quot; to import your
          data.
        </p>
      </Card>

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
                <TableHead>Vaults</TableHead>
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
                            {provider?.name || connection.source_type}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {connection.external_account_id ||
                              connection.nango_connection_id}
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {connection.vault_ids.length > 0 ? (
                          connection.vault_ids.map((vaultId) => (
                            <Badge key={vaultId} variant="outline">
                              {getVaultName(vaultId)}
                            </Badge>
                          ))
                        ) : (
                          <span className="text-sm text-muted-foreground">
                            No vaults
                          </span>
                        )}
                      </div>
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
                            ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
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
                      <div className="flex justify-end gap-2">
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
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDeleteConnection(connection)}
                          className="text-red-600 hover:bg-red-50 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        open={!!deleteConnection}
        onOpenChange={() => setDeleteConnection(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete integration?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove the{" "}
              {PROVIDERS[deleteConnection?.source_type || ""]?.name ||
                deleteConnection?.source_type}{" "}
              connection. Documents already synced will remain in your
              knowledge base.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
