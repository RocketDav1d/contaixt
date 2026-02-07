"use client"

import * as React from "react"
import {
  Home,
  FolderOpen,
  Plug,
  Settings,
  HelpCircle,
} from "lucide-react"

import { NavMain } from "@/components/nav-main"
import { NavUser } from "@/components/nav-user"
import { WorkspaceSwitcher } from "@/components/workspace-switcher"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"

const navPlatform = [
  {
    title: "Overview",
    url: "/overview",
    icon: Home,
  },
  {
    title: "Context Vaults",
    url: "/vaults",
    icon: FolderOpen,
  },
  {
    title: "Integrations",
    url: "/integrations",
    icon: Plug,
  },
]

const navSettings = [
  {
    title: "Workspace Settings",
    url: "/settings",
    icon: Settings,
  },
  {
    title: "Help",
    url: "/help",
    icon: HelpCircle,
  },
]

interface AppSidebarProps extends React.ComponentProps<typeof Sidebar> {
  user?: {
    email?: string
    name?: string
    avatar?: string
  }
  workspace?: {
    id: string
    name: string
  }
}

export function AppSidebar({ user, workspace, ...props }: AppSidebarProps) {
  return (
    <Sidebar variant="floating" {...props}>
      <SidebarHeader>
        <WorkspaceSwitcher
          workspace={workspace || { id: "default", name: "My Workspace" }}
        />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={navPlatform} label="Platform" />
        <NavMain items={navSettings} label="Settings" />
      </SidebarContent>
      <SidebarFooter>
        <NavUser
          user={user || { email: "user@example.com" }}
        />
      </SidebarFooter>
    </Sidebar>
  )
}
