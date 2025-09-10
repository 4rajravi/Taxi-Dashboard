"use client";

import { ArrowRightIcon, Radio } from "lucide-react";

import Link from "next/link";

import IncidentLiveFeed from "@/components/incidents/incident-live-feed";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
} from "@/components/ui/sidebar";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

// Sidebar component for displaying live incidents feed
export function AppSidebar() {
  return (
    <Sidebar>
      {/* Sidebar header with title and history link icon with tooltip */}
      <SidebarHeader className="py-3 px-2 bg-white border-0">
        <div className="flex items-center justify-between px-2 text-s font-semibold">
          <div className="flex items-center gap-2 text-slate-500 text-xs">
            <Radio />
            <div className="flex flex-col items-start mt-1">
              <h4 className="text-base text-black">Live Incidents Feed</h4>
              <Label className="text-xs font-light text-slate-400">
                Shows the latest 50 incidents
              </Label>
            </div>
          </div>
        </div>
      </SidebarHeader>
      {/* Sidebar content with incident feed */}
      <SidebarContent className="px-2 bg-white">
        <SidebarGroup>
          <SidebarGroupContent>
            <IncidentLiveFeed />
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="px-2 py-2 bg-white border-0">
        <Link href="/incidents" target="_blank" rel="noopener noreferrer">
          <Button
            variant="link"
            className="text-slate-500 text-sm font-normal cursor-pointer"
          >
            View Incident History
            <ArrowRightIcon />
          </Button>
        </Link>
      </SidebarFooter>
    </Sidebar>
  );
}
