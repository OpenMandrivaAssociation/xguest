Summary: Creates xguest user as a locked down user 
Name: xguest
Version: 1.0.10
Release: 9
License: GPLv2+
Group:   System/Base
BuildArch: noarch
Source0:  http://people.fedoraproject.org/~dwalsh/xguest/%{name}-%{version}.tar.bz2
Source10: mkxguesthome
# (tv) prevent accessing other people accounts:
patch1: xguest-namespace2.patch
URL:     http://people.fedoraproject.org/~dwalsh/xguest/

Requires(pre): pam >= 0.99.8.1 
Requires: dm

%define grp_option -U

# TODO:
# - check if /usr/sbin/gdm-safe-restart is needed in /etc/X11.gdm/PostSession/Default
# - prevent logging on console

%description
Installing this package sets up the xguest user to be used as a temporary
account to switch to or as a kiosk user account.
The user is only allowed to log in via gdm.  The home and temporary directories
of the user will be polyinstantiated and mounted on tmpfs.

WARNING: unlike Fedora, where the account is disabled unless SELinux is in
enforcing mode and where it's only accessible through gdm/kdm/xdm, it's
accessible from the console too.

%prep
%setup -q
%patch1 -p1 -b .home

%install
rm -fR %{buildroot}
%{__mkdir} -p %{buildroot}/%{_sysconfdir}/desktop-profiles
%{__mkdir} -p %{buildroot}/%{_sysconfdir}/security/namespace.d/ls
install -m0644 xguest.zip %{buildroot}/%{_sysconfdir}/desktop-profiles/
install -m0644 xguest.conf %{buildroot}/%{_sysconfdir}/security/namespace.d/

install -m0755 %{SOURCE10} %{buildroot}%{_sysconfdir}/security/namespace.d/

# (tv) Using UID higher than UID_MAX=60000 from /etc/login.defs:
mkdir -p %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/xguest-add-helper <<EOF
#!/bin/sh
groupdel xguest 2>/dev/null
userdel -r xguest 2>/dev/null

useradd -s /bin/rbash -K UID_MIN=61000 -K UID_MAX=65000 -K GID_MIN=61000 -K GID_MAX=65000 %grp_option -p '' -c "Guest Account" xguest || :

# prevent remote login:
if ! grep -q xguest /etc/ssh/denyusers; then
	echo xguest >> /etc/ssh/denyusers
fi

# prevent accessing most configuration tools (mcc still available with root password)
for i in /etc/pam.d/{mandriva-simple-auth,simple_root_authen,urpmi.update}; do
	grep -F -q xguest \$i && continue
	echo -e "\nauth\trequired\tpam_succeed_if.so\tquiet user != xguest" >> \$i
done
EOF

%post
if [ $1 -eq 1 ]; then
	xguest-add-helper
fi

%files
%attr(755,root,root) %{_bindir}/*
%config(noreplace) %{_sysconfdir}/desktop-profiles/xguest.zip
%{_sysconfdir}/security/namespace.d/
%doc README LICENSE

%preun
if [ $1 -eq 0 ]; then

userdel -r xguest
groupdel xguest

# remove forbiden SSH:
sed -i '/^xguest/d' /etc/ssh/denyusers

fi

%triggerun -- xguest <= 1.0.8-3mdv2010.0
userdel -r guest 2>/dev/null
xguest-add-helper
