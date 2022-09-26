Summary:	Creates xguest user as a locked down user 
Name:		xguest
Version: 	1.0.10
Release: 	17
License: 	GPLv2+
Group:   	System/Base
BuildArch: 	noarch
Source:  	http://people.fedoraproject.org/~dwalsh/xguest/%{name}-%{version}.tar.bz2
Source10: 	mkxguesthome
# (tv) prevent accessing other people accounts:
Patch1: 	xguest-namespace.patch
URL:     	http://people.fedoraproject.org/~dwalsh/xguest/

Requires(pre):	pam >= 0.99.8.1
BuildRequires:	systemd-rpm-macros

%define grp_option -U

%description
Installing this package sets up the xguest user to be used as a temporary
account to switch to or as a kiosk user account.
The user is only allowed to log in via gdm.  The home and temporary directories
of the user will be polyinstantiated and mounted on tmpfs.

WARNING: unlike Fedora, where the account is disabled unless SELinux is in
enforcing mode and where it's only accessible through gdm/kdm/xdm, it's
accessible from the console too.

%prep
%autosetup -p1

%build

%install
mkdir -p %{buildroot}/%{_sysconfdir}/desktop-profiles
mkdir -p %{buildroot}/%{_sysconfdir}/security/namespace.d/
install -m0644 xguest.zip %{buildroot}/%{_sysconfdir}/desktop-profiles/
install -m0644 xguest.conf %{buildroot}/%{_sysconfdir}/security/namespace.d/

install -m0755 %{SOURCE10} %{buildroot}%{_sysconfdir}/security/namespace.d/

mkdir -p %{buildroot}%{_sysusersdir}
cat >%{buildroot}%{_sysusersdir}/xguest.conf <<EOF
g xguest - -
u xguest - "Guest User" /home/xguest %{_bindir}/rbash
EOF

mkdir -p %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/xguest-add-helper <<EOF
#!/bin/sh
case \$(env | grep -m 1 -i lang | cut -d= -f2 | cut -d. -f1) in
	fr_FR) comment_xguest="Compte invité";;
	de_DE) comment_xguest="Gast-Zugang";;
	es_ES) comment_xguest="Cuenta invitado";;
	it_IT) comment_xguest="Utente Ospite";;
	pl_PL) comment_xguest="Konto gościa";;
	pt_PT) comment_xguest="Conta convidado";;
	*) comment_xguest="Guest Account";;
esac
[ "$comment_xguest" != "Guest User" ] && sed -i -e "s,Guest User,$comment_xguest," %{_sysusersdir}/xguest.conf

# prevent remote login:
if [ -e /etc/ssh/denyusers ]; then
	if ! grep -q xguest /etc/ssh/denyusers; then
		echo xguest >> /etc/ssh/denyusers
	fi
fi

# prevent accessing most configuration tools (mcc still available with root password)
for i in /etc/pam.d/{mandriva-simple-auth,simple_root_authen}; do
	if [ -e \$i ]; then
		grep -F -q xguest \$i && continue
	fi
	echo -e "\nauth\trequired\tpam_succeed_if.so\tquiet user != xguest" >> \$i
done
EOF

%post
if [ $1 -eq 1 ]; then
	xguest-add-helper
fi

%preun
if [ $1 -eq 0 ]; then
	# remove forbiden SSH:
	sed -i '/^xguest/d' /etc/ssh/denyusers
fi

%triggerin -- openssh-server
if ! grep -q xguest /etc/ssh/denyusers; then
  echo xguest >> /etc/ssh/denyusers
fi

%files
%attr(755,root,root) %{_bindir}/*
%dir %{_sysconfdir}/desktop-profiles
%config(noreplace) %{_sysconfdir}/desktop-profiles/xguest.zip
%{_sysconfdir}/security/namespace.d/
%{_sysusersdir}/xguest.conf
%doc README LICENSE
