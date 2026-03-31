export interface SidebarItem {
  header?: boolean
  text?: string
  divider?: boolean
  dc?: boolean
  group?: boolean
  icon?: string
  path?: string
  items?: SidebarItem[]
}
