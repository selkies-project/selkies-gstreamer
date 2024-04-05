/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 *
 * This file incorporates work covered by the following copyright and
 * permission notice:
 *
 *   Copyright 2019 Google Inc. All rights reserved.
 *
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *        http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 */

package main

import (
	"context"
	"crypto/hmac"
	"crypto/sha1"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"time"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/util/homedir"

	metadata "cloud.google.com/go/compute/metadata"
	htpasswd "github.com/tg123/go-htpasswd"
)

type rtcConfigResponse struct {
	LifetimeDuration   string              `json:"lifetimeDuration"`
	IceServers         []iceServerResponse `json:"iceServers"`
	BlockStatus        string              `json:"blockStatus"`
	IceTransportPolicy string              `json:"iceTransportPolicy"`
}

type iceServerResponse struct {
	URLs       []string `json:"urls"`
	Username   string   `json:"username,omitempty"`
	Credential string   `json:"credential,omitempty"`
}

type ConcurrentSlice struct {
	sync.RWMutex
	items []interface{}
}

type ConcurrentMap struct {
	sync.RWMutex
	items map[string]interface{}
}

func main() {
	externalIP := popVarFromEnv("EXTERNAL_IP", false, getMyExternalIP())
	turnPort := popVarFromEnv("TURN_PORT", false, "80")
	turnAltPort := popVarFromEnv("TURN_ALT_PORT", false, "443")
	sharedSecret := popVarFromEnv("TURN_SHARED_SECRET", true, "")
	htpasswdFilePath := popVarFromEnv("TURN_HTPASSWD_FILE", false, "")
	listenPort := popVarFromEnv("PORT", false, "8080")
	authHeaderName := strings.ToLower(popVarFromEnv("AUTH_HEADER_NAME", false, "x-auth-user"))

	// Env var for running in aggregator mode with K8s Endpoints discovery.
	endpointsDiscoveryName := popVarFromEnv("DISCOVERY_ENDPOINTS_NAME", false, "")
	endpointsDiscoveryNamespace := popVarFromEnv("DISCOVERY_ENDPOINTS_NAMESPACE", false, "")
	endpointsDiscoverySrvServiceName := popVarFromEnv("DISCOVERY_ENDPOINTS_SRV_SERVICE_NAME", false, "")

	// Env vars to run in managed instance group aggregator mode.
	migFilterPattern := popVarFromEnv("MIG_DISCO_FILTER", false, "")
	migDiscoveryProjectID := popVarFromEnv("MIG_DISCO_PROJECT_ID", false, "")

	// Make sure at least one external IP method was found.
	if len(externalIP) == 0 && len(endpointsDiscoveryName) == 0 && len(migFilterPattern) == 0 {
		log.Fatalf("ERROR: no EXTERNAL_IP, DISCOVERY_DNS_NAME, or MIG_DISCO_FILTER was not found, cannot continue.")
	}

	// Flags used for connecting out-of-cluster.
	var kubeconfig *string
	if home := homedir.HomeDir(); home != "" {
		kubeconfig = flag.String("kubeconfig", filepath.Join(home, ".kube", "config"), "(optional) absolute path to the kubeconfig file")
	} else {
		kubeconfig = flag.String("kubeconfig", "", "absolute path to the kubeconfig file")
	}
	flag.Parse()

	// Kubernetes client config to watch service Endpoints
	// Try in-cluster config
	running_on_k8s := true
	config, err := rest.InClusterConfig()
	if err == nil {
		log.Printf("using in-cluster-config")
	} else {
		// Try out-of-cluster config
		outOfClusterConfig, err := clientcmd.BuildConfigFromFlags("", *kubeconfig)
		if err != nil {
			running_on_k8s = false
		}
		log.Printf("using out-of-cluster-config")
		config = outOfClusterConfig
	}

	var clientset *kubernetes.Clientset
	if running_on_k8s {
		// Create the Kubernetes client
		clientset, err = kubernetes.NewForConfig(config)
		if err != nil {
			log.Panic(err.Error())
			os.Exit(1)
		}
	}

	// Start background file watcher for MIG discovery method.
	migDiscoIPs := &migDiscoIPsSync{}
	if len(migFilterPattern) > 0 {
		var err error
		if len(migDiscoveryProjectID) == 0 {
			migDiscoveryProjectID, err = metadata.ProjectID()
			if err != nil {
				log.Fatalf("%v", err)
			}
		}
		migDiscoIPs.ProjectID = migDiscoveryProjectID
		migDiscoIPs.FilterPattern = regexp.MustCompile(migFilterPattern)

		log.Printf("Discovering TURN ips from GCE Managed Instance Group named: %s in project %s", migFilterPattern, migDiscoveryProjectID)

		// Perform initial check
		migDiscoIPs.Update()

		// Update discovery SRV service.
		updateDiscoverySRVService(clientset, endpointsDiscoverySrvServiceName, endpointsDiscoveryNamespace, migDiscoIPs.ExternalIPs)
	}

	// Parse optional htpasswd file for authorization.
	var htpasswdFile *htpasswd.File
	if len(htpasswdFilePath) > 0 {
		if _, err := os.Stat(htpasswdFilePath); os.IsNotExist(err) {
			log.Fatalf("htaccess file not found")
		}
		var err error
		htpasswdFile, err = htpasswd.New(htpasswdFilePath, htpasswd.DefaultSystems, nil)
		if err != nil {
			log.Fatalf("ERROR: failed to read htpasswd file: %v", err)
		}
		log.Printf("INFO: htaccess file read in provided path")
		log.Printf("INFO: forcing auth header to: 'authorization' for basic authentication with htaccess file")
		authHeaderName = "authorization"
	}

	// Slice of external IPs in use by coturn pods.
	// Updated by informer handlers.
	endpointsIPsSync := ConcurrentSlice{
		items: make([]interface{}, 0),
	}

	// Map of K8S node names to external IPs.
	// Updated by informer handlers.
	nodeIPsSync := ConcurrentMap{
		items: make(map[string]interface{}, 0),
	}

	if len(endpointsDiscoveryName) > 0 && len(endpointsDiscoveryNamespace) > 0 {
		// Running in endpoints discovery mode.
		// This mode runs in a kubernetes cluster and watches changes to the Endpoints and Nodes.
		// coturn pods added to the endpoints are matched to a node and the node External IP is used as the advertised TURN host.

		nodeInformer := StartNodesInformer(clientset,
			// Add func
			func(node *corev1.Node) {
				externalIP := ""
				for _, address := range node.Status.Addresses {
					if address.Type == corev1.NodeExternalIP {
						externalIP = address.Address
						break
					}
				}
				if len(externalIP) > 0 {
					log.Printf("Found new node with external IP: %s: %s", node.Name, externalIP)
					nodeIPsSync.Lock()
					defer nodeIPsSync.Unlock()
					nodeIPsSync.items[node.Name] = externalIP
				} else {
					log.Printf("WARN: Node has no external IP: %s", node.Name)
				}
			},
			// Delete func
			func(node *corev1.Node) {
				log.Printf("Node was deleted: %s", node.Name)
				nodeIPsSync.Lock()
				defer nodeIPsSync.Unlock()
				delete(nodeIPsSync.items, node.Name)
			},
			// Update func
			func(oldNode, newNode *corev1.Node) {
				externalIP := ""
				for _, address := range newNode.Status.Addresses {
					if address.Type == corev1.NodeExternalIP {
						externalIP = address.Address
						break
					}
				}
				if len(externalIP) > 0 {
					if ip, ok := nodeIPsSync.items[newNode.Name]; ok {
						if ip == externalIP {
							// IP didn't change.
							return
						}
					}
					log.Printf("Found new node with external IP: %s: %s", newNode.Name, externalIP)
					nodeIPsSync.Lock()
					defer nodeIPsSync.Unlock()
					nodeIPsSync.items[newNode.Name] = externalIP
				} else {
					log.Printf("WARN: Node has no external IP: %s", newNode.Name)
				}
			},
		)
		defer close(nodeInformer)

		getNodesFromEP := func(ep *corev1.Endpoints) []string {
			nodeNames := []string{}
			for _, subset := range ep.Subsets {
				for _, address := range subset.Addresses {
					if address.NodeName != nil {
						nodeNames = append(nodeNames, *address.NodeName)
					}
				}
			}
			return nodeNames
		}

		epInformer := StartEndpointsInformer(clientset,
			// Add func
			func(ep *corev1.Endpoints) {
				if ep.Namespace != endpointsDiscoveryNamespace || ep.Name != endpointsDiscoveryName {
					return
				}
				nodeNames := getNodesFromEP(ep)
				if len(nodeNames) > 0 {
					endpointsIPsSync.Lock()
					defer endpointsIPsSync.Unlock()
					nodeIPsSync.Lock()
					defer nodeIPsSync.Unlock()

					// Reset the list of IPs.
					endpointsIPsSync.items = make([]interface{}, 0)
					ips := make([]string, 0)

					// Add all node IPs to the list of endpoints IPs.
					for _, nodeName := range nodeNames {
						if nodeIP, ok := nodeIPsSync.items[nodeName]; ok {
							// Add IP to the list.
							log.Printf("Adding external IP: %s", nodeIP)
							endpointsIPsSync.items = append(endpointsIPsSync.items, nodeIP)
							ips = append(ips, nodeIP.(string))
						}
					}
					// Update discovery SRV service.
					updateDiscoverySRVService(clientset, endpointsDiscoverySrvServiceName, endpointsDiscoveryNamespace, ips)
				} else {
					log.Printf("Endpoint found but has no subsets or nodes")
				}
			},
			// Delete func
			func(ep *corev1.Endpoints) {
				if ep.Namespace != endpointsDiscoveryNamespace || ep.Name != endpointsDiscoveryName {
					return
				}
				log.Printf("Endpoint was deleted: %s", ep.Name)

				// Reset the list of IPs.
				log.Printf("Removing all external IPs because Endpoint was deleted.")
				endpointsIPsSync.items = make([]interface{}, 0)
				// Update discovery SRV service.
				updateDiscoverySRVService(clientset, endpointsDiscoverySrvServiceName, endpointsDiscoveryNamespace, []string{})
			},
			// Update func
			func(oldep *corev1.Endpoints, newep *corev1.Endpoints) {
				if oldep.Namespace != endpointsDiscoveryNamespace || oldep.Name != endpointsDiscoveryName {
					return
				}
				log.Printf("Endpoint was updated: %s", newep.Name)

				nodeNames := getNodesFromEP(newep)

				endpointsIPsSync.Lock()
				defer endpointsIPsSync.Unlock()
				nodeIPsSync.Lock()
				defer nodeIPsSync.Unlock()

				// Reset the list of IPs.
				endpointsIPsSync.items = make([]interface{}, 0)
				ips := make([]string, 0)

				// Add all node IPs to the list of endpoints IPs.
				for _, nodeName := range nodeNames {
					if nodeIP, ok := nodeIPsSync.items[nodeName]; ok {
						// Add IP to the list.
						log.Printf("Adding external IP: %s", nodeIP)
						endpointsIPsSync.items = append(endpointsIPsSync.items, nodeIP)
						ips = append(ips, nodeIP.(string))
					}
				}
				// Update discovery SRV service.
				updateDiscoverySRVService(clientset, endpointsDiscoverySrvServiceName, endpointsDiscoveryNamespace, ips)
			},
		)
		defer close(epInformer)
	}

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		// Get user from auth header.
		authHeaderValue := r.Header.Get(authHeaderName)
		user := ""

		// Perform basic authentication
		if authHeaderName == "authorization" {
			if strings.Contains(authHeaderValue, "Basic") {
				username, password, authOK := r.BasicAuth()
				if authOK == false {
					writeStatusResponse(w, http.StatusUnauthorized, "Invalid basic authentication credential.")
					return
				}
				// Authorize user from htpasswd file.
				if ok := htpasswdFile.Match(username, password); !ok {
					writeStatusResponse(w, http.StatusUnauthorized, "Unauthorized")
					return
				}
				user = username
			} else {
				w.Header().Set("WWW-Authenticate", `Basic realm="restricted", charset="UTF-8"`)
				writeStatusResponse(w, http.StatusUnauthorized, "Missing Authorization")
				return
			}
		} else if authHeaderName == "x-goog-authenticated-user-email" {
			// IAP uses a prefix of accounts.google.com:email, remove this to just get the email
			userToks := strings.Split(authHeaderValue, ":")
			if len(userToks) > 1 {
				user = userToks[len(userToks)-1]
			}
		} else {
			user = authHeaderValue
		}
		if len(user) == 0 {
			writeStatusResponse(w, http.StatusUnauthorized, fmt.Sprintf("Failed to get user from auth header: '%s'", authHeaderName))
			return
		}

		ips := make([]string, 0)

		if len(migFilterPattern) > 0 {
			// MIG discovery mode, use IPs found on MIG instnaces.
			migDiscoIPs.Update()
			migDiscoIPs.Lock()
			for _, ip := range migDiscoIPs.ExternalIPs {
				ips = append(ips, ip)
			}
			// Update discovery SRV service.
			updateDiscoverySRVService(clientset, endpointsDiscoverySrvServiceName, endpointsDiscoveryNamespace, migDiscoIPs.ExternalIPs)

			migDiscoIPs.Unlock()
		} else if len(endpointsDiscoveryName) > 0 && len(endpointsDiscoveryNamespace) > 0 {
			// Kubernetes endpoints discovery mode, get ips from concurent slice.
			ips = make([]string, 0)
			endpointsIPsSync.Lock()
			for _, ip := range endpointsIPsSync.items {
				ips = append(ips, ip.(string))
			}
			endpointsIPsSync.Unlock()
		} else if len(externalIP) > 0 {
			// Standard mode, use own external IP to return single server.
			ips = []string{externalIP}
		} else {
			log.Printf("ERROR: failed to match aggregator mode.")
			writeStatusResponse(w, http.StatusInternalServerError, "Internal server error")
			return
		}

		// Create the RTC config from the list of IPs
		resp, err := makeRTCConfig(ips, turnPort, turnAltPort, user, sharedSecret)
		if err != nil {
			writeStatusResponse(w, http.StatusInternalServerError, fmt.Sprintf("failed to make RTC config: %v", err))
			return
		}
		writeJSONResponse(w, http.StatusOK, resp)
		return
	})

	log.Println(fmt.Sprintf("Listening on port %s", listenPort))
	http.ListenAndServe(fmt.Sprintf("0.0.0.0:%s", listenPort), nil)
}

func makeRTCConfig(ips []string, turnPort, turnAltPort, user, secret string) (rtcConfigResponse, error) {
	var resp rtcConfigResponse
	var err error

	if len(ips) == 0 {
		return resp, fmt.Errorf("No RTC config IPs available")
	}

	username, credential := makeCredential(secret, user)

	stunURLs := []string{}
	turnURLs := []string{}

	for _, ip := range ips {
		stunURLs = append(stunURLs, fmt.Sprintf("stun:%s:%s", ip, turnPort))
		stunURLs = append(stunURLs, fmt.Sprintf("stun:%s:%s", ip, turnAltPort))
		turnURLs = append(turnURLs, fmt.Sprintf("turn:%s:%s?transport=tcp", ip, turnPort))
		turnURLs = append(turnURLs, fmt.Sprintf("turn:%s:%s?transport=tcp", ip, turnAltPort))
		turnURLs = append(turnURLs, fmt.Sprintf("turn:%s:%s?transport=udp", ip, turnPort))
		turnURLs = append(turnURLs, fmt.Sprintf("turn:%s:%s?transport=udp", ip, turnAltPort))
	}

	resp.LifetimeDuration = "86400s"
	resp.BlockStatus = "NOT_BLOCKED"
	resp.IceTransportPolicy = "all"
	resp.IceServers = []iceServerResponse{
		iceServerResponse{
			URLs: stunURLs,
		},
		iceServerResponse{
			URLs:       turnURLs,
			Username:   username,
			Credential: credential,
		},
	}

	return resp, err
}

// Creates credential per coturn REST API docs
// https://github.com/coturn/coturn/wiki/turnserver#turn-rest-api
// [START makeCredential]
func makeCredential(secret, user string) (string, string) {
	var username string
	var credential string

	ttlOneDay := 24 * 3600 * time.Second
	nowPlusTTL := time.Now().Add(ttlOneDay).Unix()
	// Make sure to set --rest-api-separator="-" in the coturn config.
	username = fmt.Sprintf("%d-%s", nowPlusTTL, user)

	mac := hmac.New(sha1.New, []byte(secret))
	mac.Write([]byte(username))
	credential = base64.StdEncoding.EncodeToString(mac.Sum(nil))

	return username, credential
}

// [END makeCredential]

// Authoritative update of the Endpoints of a given Kubernetes Service with the provided list of external IPs.
func updateDiscoverySRVService(clientset *kubernetes.Clientset, serviceName, namespace string, ips []string) {
	if len(serviceName) == 0 {
		return
	}

	log.Printf("Updating discovery service: %s/%s with %d ips", namespace, serviceName, len(ips))

	epClient := clientset.CoreV1().Endpoints(namespace)

	endpoints := &corev1.Endpoints{
		ObjectMeta: metav1.ObjectMeta{
			Name:      serviceName,
			Namespace: namespace,
		},
		Subsets: []corev1.EndpointSubset{},
	}

	for _, ip := range ips {
		subset := corev1.EndpointSubset{
			Addresses: []corev1.EndpointAddress{
				corev1.EndpointAddress{
					IP: ip,
				},
			},
			Ports: []corev1.EndpointPort{
				corev1.EndpointPort{
					Name:     "turn",
					Protocol: corev1.ProtocolUDP,
					Port:     3478,
				},
			},
		}
		endpoints.Subsets = append(endpoints.Subsets, subset)
	}

	context := context.TODO()

	_, err := epClient.Update(context, endpoints, metav1.UpdateOptions{})
	if err != nil {
		log.Printf("ERROR: failed to update endpoints on service %s/%s: %v", namespace, serviceName, err)
	}
}

func writeStatusResponse(w http.ResponseWriter, statusCode int, message string) {
	type statusResponse struct {
		Status string
	}
	status := statusResponse{
		Status: message,
	}
	writeJSONResponse(w, statusCode, status)
}

func writeJSONResponse(w http.ResponseWriter, statusCode int, data interface{}) error {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	enc := json.NewEncoder(w)
	enc.SetIndent("", "  ")
	return enc.Encode(data)
}

func getInstanceExternalIP(uri, accessToken string) (string, error) {
	ip := ""
	type accessConfig struct {
		NatIP string `json:"natIP"`
	}
	type networkInterface struct {
		AccessConfigs []accessConfig `json:"accessConfigs"`
	}
	type getInstanceReponse struct {
		NetworkInterfaces []networkInterface `json:"networkInterfaces"`
	}

	client := &http.Client{}
	req, err := http.NewRequest("GET", uri, nil)
	req.Header.Set("User-Agent", "Selkies_Controller/1.0")
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", accessToken))
	resp, err := client.Do(req)
	if err != nil {
		return ip, err
	}

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return ip, err
	}

	var getResp getInstanceReponse
	if err := json.Unmarshal(body, &getResp); err != nil {
		return ip, err
	}
	if len(getResp.NetworkInterfaces) > 0 && len(getResp.NetworkInterfaces[0].AccessConfigs) > 0 && len(getResp.NetworkInterfaces[0].AccessConfigs[0].NatIP) > 0 {
		ip = getResp.NetworkInterfaces[0].AccessConfigs[0].NatIP
	}

	return ip, nil
}

func getMyExternalIP() string {
	// Obtain external IP from Google DNS TXT record.
	r := &net.Resolver{
		PreferGo: true,
		Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
			d := net.Dialer{
				Timeout: time.Millisecond * time.Duration(10000),
			}
			return d.DialContext(ctx, network, "ns1.google.com:53")
		},
	}
	ips, _ := r.LookupTXT(context.Background(), "o-o.myaddr.l.google.com")
	if len(ips) > 0 {
		return ips[0]
	}
	return ""
}

func popVarFromEnv(envName string, isRequired bool, defaultValue string) string {
	value := os.Getenv(envName)
	if isRequired && len(value) == 0 {
		log.Fatalf("Missing environment variable: %s", envName)
	} else if len(value) == 0 {
		value = defaultValue
	}
	return strings.TrimSpace(value)
}
